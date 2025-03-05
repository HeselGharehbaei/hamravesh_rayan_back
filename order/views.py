from itertools import groupby
from operator import attrgetter
from jsonschema import ValidationError
import qrcode
import io
import json
import requests
import pandas as pd
from collections import Counter
from jalali_date import datetime2jalali

from django.utils.translation import gettext as _
from django.db.models import Count, F, IntegerField
from django.views import View
from django.core.files.base import ContentFile
from django.shortcuts import get_list_or_404, get_object_or_404
from django.db.models.functions import Round, Cast

from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, permissions
from rest_framework.views import APIView

from cities.models import City, State
from core.utils.constant import site
from core.utils.constant import tax_co
from config.settings import API_KEY
from business.models import Business
from payment.models import IncreaseWalletCo, Wallet,PaymentAmount
from usermodel.models import CustomUser
from userprofile.models import LegalUserProfile, RealUserProfile
from .models import Order, QRCode
from .serializers import *

def sendCancelSmsC(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'template': 'cancelorderycust'
    }
    res = requests.post(url, data)

def sendCancelWaitingSmsC(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'template': 'cancelwaitingorder'
    }
    res = requests.post(url, data)

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()


class OrderUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = 'tracking_code'

    @staticmethod
    def get_restricted_fields():
        try:
            order_model = apps.get_model('order', 'Order')
        except LookupError:
            raise serializers.ValidationError('Order model could not be found.')

        all_fields = [field.name for field in order_model._meta.fields]
        return [
            field for field in all_fields
            if "receiver" not in field.lower() and "sender" not in field.lower()
        ]

    def validate_business(self, orders, user):
        """
        Validates that the user is authorized to update the given orders.
        """
        if not orders.exists():
            raise ValidationError("No orders found with the provided tracking code.")

        bus_id = orders.first().user_business.id
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()

        if legal:
            return get_object_or_404(Business, id=bus_id, legal_profile=legal)
        elif real:
            return get_object_or_404(Business, id=bus_id, real_profile=real)
        else:
            raise ValidationError('ابتدا پروفایل خود را تکمیل کنید')

    def update(self, request, *args, **kwargs):
        tracking_code = self.kwargs.get('tracking_code')
        orders = Order.objects.filter(tracking_code=tracking_code)

        # Validate business
        business = self.validate_business(orders, request.user)

        # Check if the business matches
        if not (
            orders.first().user_business.legal_profile == business.legal_profile or
            orders.first().user_business.real_profile == business.real_profile
        ):
            raise ValidationError('کاربر اجازه تغییر ندارد')

        # Prepare data
        data = request.data.copy()
        restricted_fields = self.get_restricted_fields()

        # Remove restricted fields
        for field in restricted_fields:
            data.pop(field, None)

        updated_orders = []
        for order in orders:
            sender_city_id = data.pop('sender_city', None)
            receiver_city_id = data.pop('receiver_city', None)
            if sender_city_id:
                order.sender_city = get_object_or_404(City, id=sender_city_id)  # Fetch City instance
            if receiver_city_id:
                order.receiver_city = get_object_or_404(City, id=receiver_city_id)  # Fetch City instance


            # Update other fields
            for key, value in data.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            order.save()
            updated_orders.append(order)

        # Serialize updated orders
        updated_orders_data = OrderSerializer(updated_orders, many=True).data

        return Response({
            "message": "Orders updated successfully",
            "updated_orders": updated_orders_data
        }, status=status.HTTP_200_OK)


class OrderUpdateAllView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_business(self):
        user = self.request.user
        bus_id = self.kwargs.get('bus_id')
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()

        if legal:
            return get_object_or_404(Business, id=bus_id, legal_profile=legal)
        elif real:
            return get_object_or_404(Business, id=bus_id, real_profile=real)
        else:
            raise serializers.ValidationError('ابتدا پروفایل خود را تکمیل کنید') 

    def put(self, request, *args, **kwargs):
        # Fetch orders with payment_status=False
        business = self.get_business()
        orders = Order.objects.filter(
            user_business=business,
            payment_status=False,
            pursuit='waiting for payment'
        )
        if not orders.exists():
            return Response({"message": "No orders found with payment_status=False."}, status=404)

        service_id = request.data.get("service")
        value = request.data.get("value")

        if not service_id or not value:
            return Response({"error": "Both 'service' and 'value' are required."}, status=400)

        # Extract additional fields
        required_keys = ['content', 'service', 'value', 'pickup_date']
        additional_fields = {key: value for key, value in request.data.items() if key in required_keys}

        tracking_codes = set(order.tracking_code for order in orders)

        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code)
            for order in orders:
                try:
                    recalculate = False

                    # Check if service has changed
                    if str(order.service.id) != service_id:
                        recalculate = True
                        service_price = get_object_or_404(Service, id=service_id).price
                    else:
                        service_price = get_object_or_404(Service, id=order.service.id).price

                    # Check if value has changed
                    if str(order.value) != str(value):
                        recalculate = True
                        val = int(value)
                    else:
                        val = int(order.value)

                    # Process additional fields
                    for field, field_value in additional_fields.items():
                        if field == 'content':
                            field_value = get_object_or_404(Content, id=field_value)
    
                        elif field == 'service':
                            field_value = get_object_or_404(Service, id=field_value)

                        if hasattr(order, field):
                            setattr(order, field, field_value)


                    # Only recalculate if necessary
                    if recalculate:
                        size_price = float(get_object_or_404(Size, id=order.size.id).price_co) * int(service_price)

                        if order.count >= 2:
                            decrease_count = order.count - 1
                            new_price = ((int(service_price) + float(size_price)) * order.count) - (
                                (float(service_price) + (float(get_object_or_404(Size, title='کوچک').price_co) * int(service_price))) 
                                * decrease_count * 0.3
                            )
                        else:
                            new_price = (int(service_price) + int(size_price)) * order.count

                        # Recalculate insurance
                        if val < 1000000 and val > 0:
                            val_price = 2000
                        elif val >= 1000000 and val <= 20000000:
                            val_price = float(val * 0.002)
                        elif val > 20000000 and val <= 100000000:
                            val_price = float(val * 0.003)
                        else:
                            raise ValidationError("Invalid value for insurance.")

                        total_insurance = val_price
                        total_price = new_price + total_insurance

                        # Apply tax
                        total_price += tax_co * new_price

                        # Update order price fields
                        order.price = new_price
                        order.total_price = total_price
                        order.value = val  # Update value if it changed

                    # Save updated fields
                    order.save()

                except Exception as e:
                    return Response({"error": str(e), "order_id": order.id}, status=400)

        return Response({"message": "All orders recalculated successfully."}, status=200)


class OrderDecreaseMulti(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return []
        final_orders = Order.objects.filter(
            user_business=business,
            payment_status=False,
            pursuit='waiting for payment',
        ).order_by('created_at')


        return final_orders
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        decrease_amount = 0
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            for tracking_code in tracking_codes:
                orders = queryset.filter(tracking_code=tracking_code)
                total_count = sum(order.count for order in orders)
                if total_count >= 2:
                    decrease_count = int(total_count)-1
                    order = orders.last()
                    decrease_amount += ((float(order.service.price)+(float(get_object_or_404(Size, title='کوچک').price_co) * int(order.service.price)))*decrease_count*0.3)

        return Response({'decrease_amount': decrease_amount}, status=status.HTTP_200_OK)
            

class CancelOrderView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = Business.objects.filter(
                legal_profile=legal
            ).all()
        elif real:
            business = Business.objects.filter(
                real_profile=real
            ).all()
        else:
            return []
        queryset = Order.objects.filter(user_business__in=business).order_by('tracking_code')
        return queryset

    def update(self, request, *args, **kwargs):
        send_sms = False
        user = self.request.user
        if '@' in user.username:
            user_email = user.username
        else:
            user_phone = user.username
            send_sms = True
        tracking_code = request.data.get('tracking_code')
        queryset = self.get_queryset()
        orders = queryset.filter(tracking_code=tracking_code, pursuit__in=['waiting for payment', 'waiting for collection'])
        if orders:
            # sender_phone = orders.first().sender_phone
            order_number = orders.first().order_number
            tracking_code = orders.first().tracking_code
            settelments = PaymentAmount.objects.filter(user=user, tracking_code__contains=tracking_code, deposit=True)
            total_price = orders.order_by('created_at').last().total_price
            decrease_price = 0
            if settelments:
                if float(total_price)*0.01 > 6000:
                    decrease_price = 6250
                else:
                    decrease_price = float(total_price)*0.01 + 250
            
            else:
                wallet_co = get_object_or_404(
                IncreaseWalletCo
                )
                coefficient = float(wallet_co.Coefficient)
                decrease_price = float(total_price)*coefficient

            recieved_price = float(total_price) - float(decrease_price)
            last_order = orders.last()
            if last_order.pursuit == 'waiting for payment':
                waiting_collection_status = False
            else:
                waiting_collection_status = True

            for order in orders:
                order.pursuit = 'canceled'
                order.payment_status = False
                order.dispatcher_reciever = None
                order.dispatcher_sender = None
                order.save()

            if waiting_collection_status:
                wallet = Wallet.objects.filter(user=user).first()
                wallet.amount += recieved_price
                wallet.save()
                PaymentAmount.objects.create(user=user, 
                                            amount=recieved_price,
                                            tracking_code=tracking_code,
                                            authority='canceled order',
                                            payment_status='deposite to wallet',
                                            deposit=False)
                
                check_service_count= CheckServiceCount.objects.filter(
                                    pickup_date=last_order.pickup_date,
                                    service_type=last_order.service.s_type, 
                                    service_title=last_order.service.title).first()
                
                check_service_count.service_count += 1
                check_service_count.save()

                if send_sms:
                    try:
                        sendCancelSmsC(user_phone, tracking_code)
                    except:
                        pass
            
            return Response({'message':'با موفقیت تغییر یافت'}, status=status.HTTP_200_OK)
        else:
            return Response({'message':'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class CancelWaitingOrderView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = Business.objects.filter(
                legal_profile=legal
            ).all()
        elif real:
            business = Business.objects.filter(
                real_profile=real
            ).all()
        else:
            return []
        queryset = Order.objects.filter(user_business__in=business).order_by('tracking_code')
        return queryset

    def update(self, request, *args, **kwargs):
        send_sms = False
        user = self.request.user
        if '@' in user.username:
            user_email = user.username
        else:
            user_phone = user.username
            send_sms = True
        queryset = self.get_queryset()
        all_orders = queryset.filter(pursuit='waiting for collection')
        
        if all_orders:
            tracking_codes = set()
            for order in all_orders:
                tracking_codes.add(order.tracking_code)
            for tracking_code in tracking_codes:
                orders = Order.objects.filter(tracking_code=tracking_code).all()
                order_number = orders.last().order_number
                settelments = PaymentAmount.objects.filter(user=user, tracking_code__contains=tracking_code, deposit=True)
                total_price = orders.order_by('created_at').last().total_price
                decrease_price = 0
                if settelments:
                    if float(total_price)*0.01 > 6000:
                        decrease_price = 6250
                    else:
                        decrease_price = float(total_price)*0.01 + 250
                
                else:
                    wallet_co = get_object_or_404(
                    IncreaseWalletCo
                    )
                    coefficient = float(wallet_co.Coefficient)
                    decrease_price = float(total_price)*coefficient

                recieved_price = float(total_price) - float(decrease_price)
                last_order = orders.last()
                for order in orders:
                    order.pursuit = 'canceled'
                    order.payment_status = False
                    order.dispatcher_reciever = None
                    order.dispatcher_sender = None
                    order.save()
                
                wallet = Wallet.objects.filter(user=user).first()
                wallet.amount += recieved_price
                wallet.save()
                PaymentAmount.objects.create(user=user, 
                                            amount=recieved_price,
                                            tracking_code=tracking_code,
                                            authority='canceled order',
                                            payment_status='deposite to wallet',
                                            deposit=False)
                check_service_count= CheckServiceCount.objects.filter(
                                    pickup_date=last_order.pickup_date,
                                    service_type=last_order.service.s_type, 
                                    service_title=last_order.service.title).first()
                check_service_count.service_count += 1
                check_service_count.save()
            if send_sms:
                try:
                    sendCancelWaitingSmsC(user_phone, len(tracking_codes))
                except:
                    pass
            return Response({'message':'با موفقیت تغییر یافت'}, status=status.HTTP_200_OK)
        else:
            return Response({'message':'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class OrderListGroupView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()

        if legal:
            business = Business.objects.filter(legal_profile=legal, id=bus_id).first()
        elif real:
            business = Business.objects.filter(real_profile=real, id=bus_id).first()
        else:
            return None

        if business:
            return Order.objects.filter(
                user_business=business,
                payment_status=False,
                pursuit='waiting for payment'
            ).order_by('tracking_code')
        return None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if queryset is None:
            return Response({'message': 'No businesses'}, status=400)

        # Group the queryset by `tracking_code`
        grouped_queryset = groupby(queryset, key=attrgetter('tracking_code'))
        result = []

        for tracking_code, group in grouped_queryset:
            group_list = list(group)
            last_object = group_list[-1]  # Get the last object in the group
            size_counter = Counter()
            for order in group_list:
                size_counter[order.size.title] += order.count

            # Separate sizes and their counts for the response
            size_list = list(size_counter.keys())
            count_list = list(size_counter.values())

            result.append({
                'tracking_code': tracking_code,
                'last_object': OrderListSerializer(last_object).data,  # Serialize the last object
                'size': size_list,  # List of sizes
                'count': count_list,  # List of counts for each size
                'size_counter': size_counter
            })

        return Response(result)


class OrderListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            businesses = Business.objects.filter(legal_profile=legal)
            if not businesses:
                return []

        elif real:
            businesses = Business.objects.filter(real_profile=real)
            if not businesses:
                return []
        else:
            return []
        
        queryset = Order.objects.filter(user_business__in=businesses).order_by('-created_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        response_data = []
        count = 0 
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            for tracking_code in tracking_codes:
                orders = queryset.filter(tracking_code=tracking_code)
                bill = orders.order_by('created_at').last().user_business.bill
                #sum of all orders count
                count = 0
                for order in orders:
                    count += order.count
                order = orders.order_by('created_at').last()
                #these info are reapeted in allorders with the same tracking_code except total price that is the last object price
                order_number = order.order_number
                receiver = order.receiver_name
                created_at = order.created_at
                pickup_date = order.pickup_date
                total_price = order.total_price
                pursuit = order.get_pursuit_display_translated()
                receiver_name = order.receiver_name
                receiver_address = order.receiver_address
                receiver_plaque = order.receiver_plaque
                receiver_unity = order.receiver_unity
                sender_name = order.sender_name
                sender_address = order.sender_address
                sender_plaque = order.sender_plaque
                sender_unity = order.sender_unity
                business_id = order.user_business.id
                service = order.service.title
                #change date and time to jalali
                formatted_datetime_c = datetime2jalali(created_at)
                created_at = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
                response_data.append(
                    {'order_number':order_number,
                    'tracking_code':tracking_code,
                    'receiver':receiver,
                    'created_at':created_at,
                    'count':count,
                    'pickup_date':pickup_date,
                    'total_price':total_price,
                    'receiver_name':receiver_name,
                    'receiver_address':receiver_address,
                    'receiver_plaque':receiver_plaque,
                    'receiver_unity':receiver_unity,
                    'sender_name':sender_name,
                    'sender_address':sender_address,
                    'sender_plaque':sender_plaque,
                    'sender_unity':sender_unity,
                    'pursuit': pursuit,
                    'business_id': business_id,
                    'service': service,
                    'bill': bill
                    }
                )
            response_data = sorted(response_data, key=lambda x: x['created_at'], reverse=True)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response([])
    

class OrderListDetailsView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        # tracking_code = self.kwargs['code']
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return []
        unique_orders = Order.objects.filter(
            user_business=business,
            payment_status=False,
            pursuit="waiting for payment"
        ).values('tracking_code').distinct()

        # Step 2: Extract tracking codes from the unique orders
        unique_tracking_codes = [order['tracking_code'] for order in unique_orders]

        # Step 3: Retrieve all Order objects with these tracking codes
        final_orders = Order.objects.filter(tracking_code__in=unique_tracking_codes).order_by('created_at')

        return final_orders
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes =set()
        price = 0
        total_price = 0
        for order in queryset:
            tracking_codes.add(order.tracking_code)
            price += order.price
        
        for tracking_code in tracking_codes:
            order = Order.objects.filter(tracking_code=tracking_code).order_by('created_at').last()
            total_price += order.total_price
        
        insurance = total_price-price

        data = {
            'total_price':total_price,
            'price':price,
            'insurance':insurance
        }
        return Response(data)


class OrderListDetailsPaymentView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        tracking_code = self.kwargs['code']
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return []
        orders = Order.objects.filter(
            user_business=business,
            tracking_code=tracking_code,
            payment_status=False
        ).all()
        return orders
    def list(self, request, *args, **kwargs):
        orders = self.get_queryset()
        total_price = orders.order_by('created_at').last().total_price
        price = sum(order.price for order in orders)
        insurance = total_price-price
        data_out = {
            'total_price': total_price,
            'price': price,
            'insurance': insurance
        }
        return Response(data_out)


class OrderListNotPaiedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return []
        unique_orders = Order.objects.filter(
            user_business=business,
            payment_status=False,
            pursuit='waiting for payment',
        ).values('tracking_code').distinct()

        # Step 2: Extract tracking codes from the unique orders
        unique_tracking_codes = [order['tracking_code'] for order in unique_orders]

        # Step 3: Retrieve all Order objects with these tracking codes
        final_orders = Order.objects.filter(tracking_code__in=unique_tracking_codes).order_by('created_at')

        return final_orders
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        response_data = []
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            for tracking_code in tracking_codes:
                orders = queryset.filter(tracking_code=tracking_code)
                #sum of all orders count
                order = orders.order_by('created_at').last()
                #these info are reapeted in allorders with the same tracking_code except total price that is the last object price
                receiver_title = order.receiver_title
                pursuit = order.pursuit
                created_at = datetime2jalali(order.created_at).strftime('%Y/%m/%d %H:%M:%S')
                response_data.append(
                    {'tracking_code':tracking_code,
                    'receiver_title':receiver_title,
                    'pursuit':pursuit,
                    'created_at': created_at,
                    }
                )
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response([])


class OrderListSizeNotPaiedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return []
        unique_orders = Order.objects.filter(
            user_business=business,
            pursuit='waiting for payment',
            payment_status=False
        ).values('tracking_code').distinct()

        # Step 2: Extract tracking codes from the unique orders
        unique_tracking_codes = [order['tracking_code'] for order in unique_orders]

        # Step 3: Retrieve all Order objects with these tracking codes
        final_orders = Order.objects.filter(tracking_code__in=unique_tracking_codes).order_by('created_at')

        return final_orders
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        response_data = []
        small = 0
        medium = 0
        big = 0
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        for tracking_code in tracking_codes:
            orders = queryset.filter(tracking_code=tracking_code)
            #sum of all orders count
            for order in orders:
                if order.size.title =='کوچک':
                    small += order.count
                elif order.size.title =='متوسط':
                    medium += order.count
                elif order.size.title =='بزرگ':
                    big += order.count
        small_id = Size.objects.filter(title='کوچک').first().id
        medium_id = Size.objects.filter(title='متوسط').first().id
        big_id = Size.objects.filter(title='بزرگ').first().id

        response_data.append(
            {f'{small_id}':small,
            f'{medium_id}':medium,
            f'{big_id}':big
            }
        )
        return Response(response_data, status=status.HTTP_200_OK)


class PursuitOrder(APIView):
    def post(self, request, *args, **kwargs):
        tracking_code = self.request.data.get('tracking_code')
        # # Fetch the order with the given tracking code
        order = Order.objects.filter(tracking_code=tracking_code)
        if order.exists():  # Use exists() to check if any results are found
            last_order = order.order_by('created_at').last()  # Safely use .last() now
            sender_disp = last_order.dispatcher_sender
            if sender_disp:
                sender_disp = sender_disp.last_name
            else:
                sender_disp = ''
            received_time = last_order.service.delivery_time
            pursuit_status = last_order.get_pursuit_display_translated()  # Get translated pursuit status
            updated_at = last_order.updated_at
            formatted_datetime_c = datetime2jalali(updated_at)
            updated_at = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
            return Response({
                'pursuit': pursuit_status,
                'sender_disp':sender_disp,
                'received_time':received_time,
                'updated_at':updated_at,
                }, status=status.HTTP_200_OK)
        else:
            # Return 403 if no matching order is found
            return Response(
                {'message': 'کدرهگیری موجود نیست'}, 
                status=status.HTTP_403_FORBIDDEN
            )


class CountOrdersView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            businesses = Business.objects.filter(legal_profile=legal)
            if not businesses:
                return []

        elif real:
            businesses = Business.objects.filter(real_profile=real)
            if not businesses:
                return []

        else:
            return []

        queryset = Order.objects.filter(user_business__in=businesses)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            return Response({'count': len(tracking_codes)})
        else:
            return Response({'count': 0})
        

class OrderInwayListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            businesses = Business.objects.filter(legal_profile=legal)
            if not businesses:
                return Response({'message': 'No businesses'})
        elif real:
            businesses = Business.objects.filter(real_profile=real)
            if not businesses:
                return Response({'message': 'No business'})
        else:
            return []

        # Assuming 'tracking_code' is the field you want to group by
        queryset = Order.objects.filter(user_business__in=businesses,
                                         payment_status=True, 
                                         pursuit__in=['waiting for collection', 'get by ambassador', 'collected', 'waiting for distribution']).order_by('-created_at')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        response_data = []
        count = 0 
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            for tracking_code in tracking_codes:
                orders = queryset.filter(tracking_code=tracking_code)
                bill = order.user_business.bill
                #sum of all orders count
                count = 0
                for order in orders:
                    count += order.count
                order = orders.order_by('created_at').last()
                #these info are reapeted in allorders with the same tracking_code except total price that is the last object price
                receiver = order.receiver_name
                created_at = order.created_at
                pickup_date = order.pickup_date
                total_price = order.total_price
                pursuit = order.get_pursuit_display_translated()
                receiver_name = order.receiver_name
                receiver_address = order.receiver_address
                receiver_plaque = order.receiver_plaque
                receiver_unity = order.receiver_unity
                sender_name = order.sender_name
                sender_address = order.sender_address
                sender_plaque = order.sender_plaque
                sender_unity = order.sender_unity
                business_id = order.user_business.id
                order_number = order.order_number
                service = order.service.title
                #change date and time to jalali
                formatted_datetime_c = datetime2jalali(created_at)
                created_at = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
                response_data.append(
                    {'order_number':order_number,
                    'tracking_code':tracking_code,
                    'receiver':receiver,
                    'created_at':created_at,
                    'count':count,
                    'pickup_date':pickup_date,
                    'total_price':total_price,
                    'receiver_name':receiver_name,
                    'receiver_address':receiver_address,
                    'receiver_plaque':receiver_plaque,
                    'receiver_unity':receiver_unity,
                    'sender_name':sender_name,
                    'sender_address':sender_address,
                    'sender_plaque':sender_plaque,
                    'sender_unity':sender_unity,
                    'pursuit': pursuit,
                    'business_id': business_id,
                    'service': service,
                    'bill': bill

                    }
                )
            response_data = sorted(response_data, key=lambda x: x['created_at'], reverse=True)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response([])


class OrderChartCount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request,*args,**kwargs):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            businesses = Business.objects.filter(legal_profile=legal)
            if not businesses:
                return Response({'message': 'کسب و کار یافت نشد'})
        elif real:
            businesses = Business.objects.filter(real_profile=real)
            if not businesses:
                return Response({'message': 'کسب و کار یافت نشد'})
        
        else:
            return Response({'message': 'کاربر کسب و کار ندارد'})
        

        all_orders = (Order.objects.filter(user_business__in=businesses)
                    .values('tracking_code')
                    .annotate(order_count=Count('id'))
                    .order_by('tracking_code'))

        collected = all_orders.filter(pursuit='collected').count()
        waiting_for_distribution = all_orders.filter(pursuit='waiting for distribution').count()
        waiting_for_payment = all_orders.filter(pursuit='waiting for payment').count()
        waiting_for_collection = all_orders.filter(pursuit='waiting for collection').count()
        canceled = all_orders.filter(pursuit='canceled').count()
        revoke = all_orders.filter(pursuit='revoke').count()
        get_by_ambassador = all_orders.filter(pursuit='get by ambassador').count()
        delivered = all_orders.filter(pursuit='delivered').count()
        returned = all_orders.filter(pursuit='returned').count()
        # all = (waiting_for_payment + 
        # waiting_for_collection + 
        # canceled + 
        # revoke + 
        # get_by_ambassador +
        # delivered +
        # returned)

        return Response({
            'در انتظار پرداخت': waiting_for_payment,
            'در انتظار جمع آوری': waiting_for_collection,
            'لغو شده': canceled,
            'ابطال شده': revoke,
            'دریافت توسط رای پیک': get_by_ambassador,
            'تحویل شده': delivered,
            'مرجوع شده': returned,
            'جمع آوری شده': collected,
            'مرکز پردازش': waiting_for_distribution,
            # 'مجموع': all

        })
                
        
class CountInwayOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            businesses = Business.objects.filter(legal_profile=legal)
            if not businesses:
                return Response({'message': 'No businesses'})
        elif real:
            businesses = Business.objects.filter(real_profile=real)
            if not businesses:
                return Response({'message': 'No business'})
        else:
            return []

        # Assuming 'tracking_code' is the field you want to group by
        queryset = Order.objects.filter(user_business__in=businesses, payment_status=True)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()

        for order in queryset:
            if order.pursuit in ['waiting for collection', 'get by ambassador', 'collected', 'waiting for distribution']:
                tracking_codes.add(order.tracking_code)
        if tracking_codes:
            return Response({'count': len(tracking_codes)})
        else:
            return Response({'count': 0})


class OrderDeleteView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # last_order = Order.objects.filter(user_business=business, payment_status=False, pursuit='waiting for payment', pre_order=0).order_by('created_at').last()
        # tracking_code = last_order.tracking_code
        orders = Order.objects.filter(user_business=business, payment_status=False, pursuit='waiting for payment', pre_order=0)
        orders.delete()
        return Response({'message': 'حذف شد'}, status=status.HTTP_200_OK)
    

class OrderDeleteOneView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        tracking_code = self.kwargs['tracking_code']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        orders = Order.objects.filter(user_business=business, tracking_code=tracking_code, payment_status=False, pursuit='waiting for payment', pre_order=0)
        orders.delete()
        return Response({'message': 'حذف شد'}, status=status.HTTP_200_OK)


class OrderDeleteSingleView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        orders = Order.objects.filter(user_business=business, is_multi=False, payment_status=False, pursuit='waiting for payment', pre_order=0)
        orders.delete()
        return Response({'message': 'حذف شد'}, status=status.HTTP_200_OK)


class PreOrderCreate(APIView):
    def post(self, request, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        tracking_code = self.request.data.get('tracking_code')
        if tracking_code is None:
            return Response({'message': 'کد رهگیری ارسال نشده است'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        orders = Order.objects.filter(tracking_code=tracking_code, user_business=business)
        for order in orders:
            order.pre_order += 1
            order.save()

        return Response({'message': 'با موفقیت ثبت شد'})


class PreOrderDeleteView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, *args, **kwargs):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        tracking_code = self.request.data.get('tracking_code')
        if tracking_code is None:
            return Response({'message': 'کد رهگیری ارسال نشده است'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        orders = Order.objects.filter(user_business=business, tracking_code=tracking_code, payment_status=False,
                                      pre_order=1)
        orders.delete()
        return Response({'message': 'حذف شد'}, status=status.HTTP_200_OK)


class PreOrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Assuming 'tracking_code' is the field you want to group by
        queryset = Order.objects.filter(user_business=business, pre_order=1, payment_status=False).order_by(
            'tracking_code')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        grouped_queryset = groupby(queryset, key=attrgetter('tracking_code'))

        result = []
        for tracking_code, group in grouped_queryset:
            group_list = list(group)
            result.append({
                'tracking_code': tracking_code,
                'objects': OrderListSerializer(group_list, many=True).data
            })

        return Response(result)


class OrderPaiedListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        bus_id = self.kwargs['bus_id']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_object_or_404(
                Business,
                id=bus_id,
                legal_profile=legal
            )
        elif real:
            business = get_object_or_404(
                Business,
                id=bus_id,
                real_profile=real
            )
        else:
            return Response({'message': 'ابتدا پروفایل خود را تکمیل کنید'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Assuming 'tracking_code' is the field you want to group by
        queryset = Order.objects.filter(user_business=business, payment_status=True).order_by('tracking_code')
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        grouped_queryset = groupby(queryset, key=attrgetter('tracking_code'))

        result = []
        for tracking_code, group in grouped_queryset:
            group_list = list(group)
            result.append({
                'tracking_code': tracking_code,
                'objects': OrderListSerializer(group_list, many=True).data
            })

        return Response(result)


class OrderNumberTrCode(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        order_number = self.kwargs['order_num']
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_list_or_404(
                Business,
                legal_profile=legal
            )
        elif real:
            business = get_list_or_404(
                Business,
                real_profile=real
            )
        else:
            return []
        final_orders = Order.objects.filter(
            user_business__in=business,
            order_number=order_number,
            payment_status=True,
            pursuit = 'waiting for collection',
        ).order_by('created_at')


        return final_orders
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        tracking_codes = set()
        response_data = []
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        if tracking_codes:
            for tracking_code in tracking_codes:
                response_data.append(
                    {'tracking_code':tracking_code,
                    }
                )
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response([])

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert image to bytes
    img_bytes = io.BytesIO()
    qr_img.save(img_bytes, format='PNG')

    return img_bytes

def generate_and_save_qr_code(data):
    qr_image_bytes = generate_qr_code(data)
    qr_code = QRCode()
    qr_code.image.save('qrcode.png', ContentFile(qr_image_bytes.getvalue()))
    qr_code.save()
    return qr_code.image.url

class QrcodeInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code = request.data.get('tracking_code')
        orders = Order.objects.filter(tracking_code=code).all()
        data = []
        size_dict = {}

        if orders:
            for order in orders:
                if not order.payment_status:
                    return Response({'message': 'این کد رهگیری پرداخت نشده'}, status=status.HTTP_406_NOT_ACCEPTABLE)
                for count in range(1, order.count + 1):
                    qr_data = code
                    # qr_data = {'کدرهگیری': code, 'شماره_آیدی': f'{order.id}_{count}', 'ابعاد': order.size.title}
                    qr_image_url = generate_and_save_qr_code(qr_data)

                    if order.user_business.logo:
                        logo = f'{site}{order.user_business.logo.url}'
                    else:
                        logo = f'{site}/media/logos/logo-placeholder.png'

                    data.append({'qr_code': f'{site}{qr_image_url}', 'tracking_code': code,
                                 'logo': logo,
                                 'id_number':  f'{order.id}_{count}', 'size': order.size.title,
                                 'sender_address': order.sender_address,
                                 'sender_plaque': order.sender_plaque,
                                 'sender_unity':order.sender_unity,
                                 'sender_phone': order.sender_phone, 'sender_name': order.sender_name,
                                #  'sender_state': order.sender_state.name, 
                                 'sender_zone': order.sender_zone,
                                 'receiver_address': order.receiver_address,
                                 'receiver_plaque': order.receiver_plaque,
                                 'receiver_unity':order.receiver_unity,
                                 'receiver_phone': order.receiver_phone, 'receiver_name': order.receiver_name,
                                #  'receiver_state': order.sender_state.name,
                                 'receiver_zone': order.receiver_zone,
                                 'pickup_date': order.pickup_date,
                                 'pickup_time': order.service.pickup_time,
                                 'delivery_time': order.service.delivery_time,
                                 'address_description': order.address_description,
                                 })
                    
                size_title = order.size.title
                size_count = order.count

                size_dict[size_title] = size_count

            for dics in data:
                for key, value in size_dict.items():
                    dics[key] = value
            
            info = QrcodeInfoSerializer(data=data, many=True)
            if info.is_valid():
                serializeQrInf = info.validated_data  # Save the serializer instance
                return Response(serializeQrInf, status=status.HTTP_200_OK)
            else:
                return Response(info.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'کد پیگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class MultiQrcodeInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_number = request.data.get('order_number')
        orders_N = Order.objects.filter(order_number=order_number).all()
        data = []
        tracking_codes = orders_N.values_list('tracking_code', flat=True).distinct()
        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code).all()
            size_dict = {}
            if orders:
                for order in orders:
                    if not order.payment_status:
                        return Response({'message': 'این کد رهگیری پرداخت نشده'}, status=status.HTTP_406_NOT_ACCEPTABLE)
                    for count in range(1, order.count + 1):
                        code = order.tracking_code
                        qr_data = {'کدرهگیری': code, 'شماره_آیدی': f'{order.id}_{count}', 'ابعاد': order.size.title}
                        qr_image_url = generate_and_save_qr_code(qr_data)

                        if order.user_business.logo:
                            logo = f'{site}{order.user_business.logo.url}'
                        else:
                            logo = f'{site}/media/logos/logo-placeholder.png'

                        data.append({'qr_code': f'{site}{qr_image_url}', 'tracking_code': code,
                                    'logo': logo,
                                    'id_number':  f'{order.id}_{count}', 'size': order.size.title,
                                    'sender_address': order.sender_address,
                                    'sender_plaque': order.sender_plaque,
                                    'sender_unity':order.sender_unity,
                                    'sender_phone': order.sender_phone, 'sender_name': order.sender_name,
                                    #  'sender_state': order.sender_state.name, 
                                    'sender_zone': order.sender_zone,
                                    'receiver_address': order.receiver_address,
                                    'receiver_plaque': order.receiver_plaque,
                                    'receiver_unity':order.receiver_unity,
                                    'receiver_phone': order.receiver_phone, 'receiver_name': order.receiver_name,
                                    #  'receiver_state': order.sender_state.name,
                                    'receiver_zone': order.receiver_zone,
                                    'pickup_date': order.pickup_date,
                                    'pickup_time': order.service.pickup_time,
                                    'delivery_time': order.service.delivery_time,
                                    'address_description': order.address_description,
                                    })
                        
                    size_title = order.size.title
                    size_count = order.count

                    size_dict[size_title] = size_count
                
                #add sizes just for this trcode
                for dics in data:
                    if dics.get('tracking_code') == code:
                        for key, value in size_dict.items():
                            dics[key] = value

            else:
                return Response({'message': 'کد پیگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
                
        info = QrcodeInfoSerializer(data=data, many=True)
        if info.is_valid():
            serializeQrInf = info.validated_data  # Save the serializer instance
            return Response(serializeQrInf, status=status.HTTP_200_OK)
        else:
            return Response(info.errors, status=status.HTTP_400_BAD_REQUEST)

class MultiWaitingQrcodeInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_list_or_404(
                Business,
                legal_profile=legal
            )
        elif real:
            business = get_list_or_404(
                Business,
                real_profile=real
            )
        else:
            return Response({'message': 'کسب و کار یافت نشد'})
        
        orders_N = Order.objects.filter(user_business__in=business, pursuit='waiting for collection').all()
        data = []
        tracking_codes = orders_N.values_list('tracking_code', flat=True).distinct()
        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code).all()
            size_dict = {}
            if orders:
                for order in orders:
                    if not order.payment_status:
                        return Response({'message': 'این کد رهگیری پرداخت نشده'}, status=status.HTTP_406_NOT_ACCEPTABLE)
                    for count in range(1, order.count + 1):
                        code = order.tracking_code
                        qr_data = {'کدرهگیری': code, 'شماره_آیدی': f'{order.id}_{count}', 'ابعاد': order.size.title}
                        qr_image_url = generate_and_save_qr_code(qr_data)

                        if order.user_business.logo:
                            logo = f'{site}{order.user_business.logo.url}'
                        else:
                            logo = f'{site}/media/logos/logo-placeholder.png'

                        data.append({'qr_code': f'{site}{qr_image_url}', 'tracking_code': code,
                                    'logo': logo,
                                    'id_number':  f'{order.id}_{count}', 'size': order.size.title,
                                    'sender_address': order.sender_address,
                                    'sender_plaque': order.sender_plaque,
                                    'sender_unity':order.sender_unity,
                                    'sender_phone': order.sender_phone, 'sender_name': order.sender_name,
                                    #  'sender_state': order.sender_state.name, 
                                    'sender_zone': order.sender_zone,
                                    'receiver_address': order.receiver_address,
                                    'receiver_plaque': order.receiver_plaque,
                                    'receiver_unity':order.receiver_unity,
                                    'receiver_phone': order.receiver_phone, 'receiver_name': order.receiver_name,
                                    #  'receiver_state': order.sender_state.name,
                                    'receiver_zone': order.receiver_zone,
                                    'pickup_date': order.pickup_date,
                                    'pickup_time': order.service.pickup_time,
                                    'delivery_time': order.service.delivery_time,
                                    'address_description': order.address_description,
                                    })
                        
                    size_title = order.size.title
                    size_count = order.count

                    size_dict[size_title] = size_count
                
                #add sizes just for this trcode
                for dics in data:
                    if dics.get('tracking_code') == code:
                        for key, value in size_dict.items():
                            dics[key] = value

            else:
                return Response({'message': 'کد پیگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
                
        info = QrcodeInfoSerializer(data=data, many=True)
        if info.is_valid():
            serializeQrInf = info.validated_data  # Save the serializer instance
            return Response(serializeQrInf, status=status.HTTP_200_OK)
        else:
            return Response(info.errors, status=status.HTTP_400_BAD_REQUEST)
                     

# filter function
class OrderStatusListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = Business.objects.filter(
                legal_profile=legal
            ).all()
        elif real:
            business = Business.objects.filter(
                real_profile=real
            ).all()
        else:
            return []
        req_status = self.request.query_params.get('status')
        queryset = Order.objects.filter(user_business__in=business, pursuit=req_status).order_by('tracking_code')
        return queryset

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        grouped_queryset = groupby(queryset, key=attrgetter('tracking_code'))
        result = []
        for tracking_code, group in grouped_queryset:
            group_list = list(group)
            result.append({
                'tracking_code': tracking_code,
                'objects': OrderListSerializer(group_list, many=True).data
            })

        return Response(result)


#change lat and long to addresses
import requests

def get_geolocation(lat, lng):
    """
    Function to get the geolocation details from the Neshan API based on latitude and longitude.
    """
    try:
        # Define the Neshan API URL and headers
        url = f'https://api.neshan.org/v4/reverse?lat={lat}&lng={lng}'
        headers = {
            'Api-Key':'service.159b2702aa574855b1c3e68b86a67e2a',  # Replace with your API key
        }

        # Make the GET request to the API
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses


        # Parse the JSON response
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching geolocation: {e}")
        return None



class ExcelUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        user = self.request.user
        # Pass the uploaded file to ExcelUploadSerializer
        serializer = ExcelUploadSerializer(data=request.data, context={'request': request, 'view': self})
        
        if serializer.is_valid():
            # Call the method to create orders from the Excel file
            orders_created, errors = serializer.create_orders_from_excel(serializer.validated_data)
            
            if errors:
                process = ProcessExcel.objects.filter(user=user)
                process.delete()
                return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
            
            process = ProcessExcel.objects.filter(user=user)
            process.delete()
            return Response({'message': f'{len(orders_created)} سفارش با موفقیت ثبت شد!'}, status=status.HTTP_201_CREATED)
        
        process = ProcessExcel.objects.filter(user=user)
        process.delete()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProcessBarExcel(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProcessExcelSerializers
    def get_queryset(self):
        user = self.request.user
        queryset = ProcessExcel.objects.filter(user=user)
        
        # Round the 'count' field and cast it to integer
        queryset = queryset.annotate(
            rounded_count=Cast(Round(F('count')), IntegerField())  # 'count' is the field name
        )
        
        return queryset