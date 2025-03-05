import datetime
import random
import requests
import re
import jdatetime
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from jalali_date import date2jalali
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from config.settings import API_KEY
from dispatcher_order.models import CodeGenerateModel
from order.models import Order
from dispatcher_profile.models import DispatcherProfile
from dispatcher_payment.models import Wallet, IncreaseWalletCo, SettelmentWallet
from dispatcher_payment.views import ZarinpalAPI
from dispatcher.permission import IsAuthenticatedWithToken
from core.utils.constant import tax_co, sender_disp_co, receiver_disp_co
from business.models import Business
from django.db.models import Sum


def transform_time_range(input_str):
    # Define the regex pattern to extract hours from the input string
    pattern1 = r'از ساعت (\d+):\d+ تا ساعت (\d+):\d+'
    pattern2 = r'تا ساعت (\d+):\d+'
    # 'از ساعت (\d+):\d+ تا ساعت (\d+):\d+'
    
    # Search for the pattern in the input string
    match1 = re.search(pattern1, input_str)
    match2 = re.search(pattern2, input_str)
    
    if match1:
        # Extract the hours from the match groups
        start_hour = match1.group(1)
        end_hour = match1.group(2)
        
        # Format the result as required
        result = f"{start_hour}الی{end_hour}"
        return result
    if match2:
        # Extract the hours from the match groups
        start_hour = match2.group(1)
        # Format the result as required
        result = f"تا {start_hour}"
        return result

    else:
        # Return None or an appropriate message if the pattern does not match
        return "Pattern not found" 


def SendReturnCode(receptor, token, token2, token3, token10):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'token2': token2,
        'token3': token3,
        'token10': token10,
        'template': 'returncode'
    }
    res = requests.post(url, data)


def SendCancelOrderSms(receptor, token, token2, token3, token20):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'token2': token2,
        'token3': token3,
        'token20': token20,
        'template': 'cancelorder'
    }
    res = requests.post(url, data) 


# def SendDeliveryCode2Sms(receptor, token, token2, token3, token20, token10):
#     url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
#     data = {
#         'receptor': receptor,
#         'token': token,
#         'token2': token2,
#         'token3': token3,
#         'token20': token20,
#         'token10': token10,
#         'template': 'DeliveryCode2'
#     }
#     res = requests.post(url, data)

def SendDeliveryCodeSms(receptor, token, token2, token3, token20, token10):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'token2': token2,
        'token3': token3,
        'token20': token20,
        'token10': token10,
        'template': 'DeliveryCode'
    }
    res = requests.post(url, data)


def english_to_persian_number(english_str):
    # Define a mapping from English digits to Persian digits
    english_to_persian_map = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }

    # Replace each English digit with the corresponding Persian digit
    persian_str = ''.join(english_to_persian_map.get(char, char) for char in english_str)
    return persian_str


class DispSenderOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        
        # Handle cases where the user has no profile
        if not hasattr(user, 'profile'):
            return Order.objects.none()  # Return an empty queryset

        # today = datetime.date.today()
        # try:
        #     today_jalali = date2jalali(today)
        #     today_jalali = str(today_jalali).replace('-', '/')
        # except Exception as e:
        #     # Handle date conversion errors
        #     return Order.objects.none()  # Return an empty queryset

        pursuit_list = ['waiting for collection', 'revoke', 'collected']
        orders = Order.objects.filter( 
            dispatcher_sender=user.profile,
            # pickup_date=english_to_persian_number(today_jalali),
            pursuit__in=pursuit_list,
            payment_status=True
        )
        return orders

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # If queryset is empty (no orders or user has no profile)
        if not queryset.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        tracking_codes = set()
        response_data = []
        total_count_of_packages= 0
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        for tracking_code in tracking_codes:
            orders = queryset.filter(tracking_code=tracking_code)
            count = sum(order.count for order in orders)
            total_count_of_packages+= count
            order = orders.order_by('created_at').last()

            # Access the related City and District names
            sender_city_name = order.sender_city.name if order.sender_city else None
            receiver_city_name = order.receiver_city.name if order.receiver_city else None
            sender_district_name = order.sender_district if order.sender_district else None
            receiver_district_name = order.receiver_district if order.receiver_district else None
            service = order.service.title if order.service else None
            pursuit = order.get_pursuit_display_translated()
            # pursuit = order.pursuit

            response_data.append({
                'tracking_code': tracking_code,
                'business_order': order.user_business.name,
                'service': service,
                'count': count,
                'sender_address': f'{order.sender_address}, پلاک {order.sender_plaque}, واحد {order.sender_unity}',
                'sender_plaque': order.sender_plaque,
                'sender_stage': order.sender_stage,
                # 'sender_state': order.sender_state,
                'sender_city': sender_city_name,
                'sender_district': sender_district_name,
                'sender_unity': order.sender_unity,
                'sender_name': order.sender_name,
                'sender_phone': order.sender_phone,
                'sender_map_link': order.sender_map_link,
                'receiver_address': f'{order.receiver_address}, پلاک {order.receiver_plaque}, واحد {order.receiver_unity}',
                'receiver_plaque': order.receiver_plaque,
                'receiver_stage': order.receiver_stage,
                'receiver_unity': order.receiver_unity,
                # 'receiver_state': order.receiver_state,
                'receiver_city': receiver_city_name,
                'receiver_district': receiver_district_name,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'receiver_map_link': order.receiver_map_link,
                'pickup_date': order.pickup_date,
                'pickup_time': transform_time_range(order.service.pickup_time),
                'delivery_time': transform_time_range(order.service.delivery_time),
                'pursuit': pursuit,
                'price': order.total_price,
                'address_description': order.address_description
            })
        response_data.append({'total_count_of_packages':total_count_of_packages})
        return Response(response_data, status=status.HTTP_200_OK)


class DispReceiverOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        
        # Handle cases where the user has no profile
        if not hasattr(user, 'profile'):
            return Order.objects.none()  # Return an empty queryset

        today = datetime.date.today()
        try:
            today_jalali = date2jalali(today)
            today_jalali = str(today_jalali).replace('-', '/')
        except Exception as e:
            # Handle date conversion errors
            return Order.objects.none()  # Return an empty queryset

        pursuit_list = ['waiting for distribution', 'get by ambassador']
        orders = Order.objects.filter(
            dispatcher_reciever=user.profile,
            pickup_date=english_to_persian_number(today_jalali),
            pursuit__in=pursuit_list,
            payment_status=True
        )
        return orders

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        tracking_codes = set()
        response_data = []

        for order in queryset:
            tracking_codes.add(order.tracking_code)

        for tracking_code in tracking_codes:
            orders = queryset.filter(tracking_code=tracking_code)
            count = sum(order.count for order in orders)
            order = orders.order_by('created_at').last()
            
            delivery_time = order.service.delivery_time
            match = re.search(r'\b(\d{1,2}):(\d{2})\b', delivery_time)
            if match:
                hour, minute = match.groups()
                time_number = int(hour) + int(minute) / 60  # تبدیل زمان به عدد اعشاری
            else:
                return Response(
                    data={"message": "هیچ زمانی در متن پیدا نشد."},
                    status=status.HTTP_404_NOT_FOUND
                )

            sender_city_name = order.sender_city.name if order.sender_city else None
            receiver_city_name = order.receiver_city.name if order.receiver_city else None
            sender_district_name = order.sender_district if order.sender_district else None
            receiver_district_name = order.receiver_district if order.receiver_district else None
            service = order.service.title if order.service else None
            pursuit = order.get_pursuit_display_translated()

            response_data.append({
                'tracking_code': tracking_code,
                'service': service,
                'count': count,
                'sender_address': f'{order.sender_address}, پلاک {order.sender_plaque}, واحد {order.sender_unity}',
                'sender_plaque': order.sender_plaque,
                'sender_stage': order.sender_stage,
                'sender_city': sender_city_name,
                'sender_district': sender_district_name,
                'sender_unity': order.sender_unity,
                'sender_name': order.sender_name,
                'sender_phone': order.sender_phone,
                'sender_map_link': order.sender_map_link,
                'receiver_address': f'{order.receiver_address}, پلاک {order.receiver_plaque}, واحد {order.receiver_unity}',
                'receiver_plaque': order.receiver_plaque,
                'receiver_stage': order.receiver_stage,
                'receiver_unity': order.receiver_unity,
                'receiver_city': receiver_city_name,
                'receiver_district': receiver_district_name,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'receiver_map_link': order.receiver_map_link,
                'pickup_date': order.pickup_date,
                'pickup_time': transform_time_range(order.service.pickup_time),
                'delivery_time': transform_time_range(order.service.delivery_time),
                'delivery_time_num': time_number,  # عدد زمان برای مرتب‌سازی
                'pursuit': pursuit,
                'price': order.total_price,
                'address_description': order.address_description,
            })

        # 🛠️ مرتب‌سازی بر اساس تایم دلیوری
        sorted_response = sorted(response_data, key=lambda x: x['delivery_time_num'])

        # حذف کلید کمکی قبل از ارسال
        for item in sorted_response:
            item.pop('delivery_time_num')

        return Response(sorted_response, status=status.HTTP_200_OK)



class DispAllOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        
        # Handle cases where the user has no profile
        if not hasattr(user, 'profile'):
            return Order.objects.none()  # Return an empty queryset

        today = datetime.date.today()
        try:
            today_jalali = date2jalali(today)
            today_jalali = str(today_jalali).replace('-', '/')
        except Exception as e:
            # Handle date conversion errors
            return Order.objects.none()  # Return an empty queryset
        pursuit_list = ['delivered', 'returned']
        orders = Order.objects.filter(
            Q(dispatcher_sender=user.profile) | Q(dispatcher_reciever=user.profile),
            pickup_date__lte=english_to_persian_number(today_jalali),
            pursuit__in=pursuit_list,
            payment_status=True
        )
        return orders

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # If queryset is empty (no orders or user has no profile)
        if not queryset.exists():
            return Response({"message": "سفارش یا پروفایل کاربر یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        tracking_codes = set()
        response_data = []
        
        for order in queryset:
            tracking_codes.add(order.tracking_code)
        total_count = len(tracking_codes)
        for tracking_code in tracking_codes:
            orders = queryset.filter(tracking_code=tracking_code)
            count = sum(order.count for order in orders)
            order = orders.order_by('created_at').last()

            # Access the related City and District names
            sender_city_name = order.sender_city.name if order.sender_city else None
            receiver_city_name = order.receiver_city.name if order.receiver_city else None
            sender_district_name = order.sender_district if order.sender_district else None
            receiver_district_name = order.receiver_district if order.receiver_district else None
            service = order.service.title if order.service else None
            pursuit = order.get_pursuit_display_translated()
            # pursuit = order.pursuit

            response_data.append({
                'tracking_code': tracking_code,
                'service': service,
                'count': count,
                'receiver_name': order.receiver_name,
                'receiver_address': order.receiver_address,
                'sender_address': order.sender_address,
                'sender_plaque': order.sender_plaque,
                'sender_stage': order.sender_stage,
                # 'sender_state': order.sender_state,
                'sender_city': sender_city_name,
                'sender_district': sender_district_name,
                'sender_unity': order.sender_unity,
                'sender_name': order.sender_name,
                'sender_phone': order.sender_phone,
                'receiver_address': order.receiver_address,
                'receiver_plaque': order.receiver_plaque,
                'receiver_stage': order.receiver_stage,
                'receiver_unity': order.receiver_unity,
                # 'receiver_state': order.receiver_state,
                'receiver_city': receiver_city_name,
                'receiver_district': receiver_district_name,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'pickup_date': order.pickup_date,
                'pickup_time': transform_time_range(order.service.pickup_time),
                'delivery_time': transform_time_range(order.service.delivery_time),
                'pursuit': pursuit,
                'price': order.total_price,
                'address_description': order.address_description,
                'total_count':total_count
            })
        
        return Response(response_data, status=status.HTTP_200_OK)


class DispBussinessWaitingforcollectionOrders(generics.ListAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    # @property
    # def today_jalali(self):
    #     """ مقدار تاریخ امروز به صورت جلالی و به شکل متن """
    #     today = datetime.date.today()
    #     return english_to_persian_number(str(date2jalali(today)).replace('-', '/'))

    def get_queryset(self):
        user = self.request.user

        disp_prof = DispatcherProfile.objects.filter(user=user).first()
        orders = Order.objects.filter(
            # pickup_date=self.today_jalali,
            dispatcher_sender=disp_prof,
            pursuit='waiting for collection'
        )

        return orders

    def list(self, request, *args, **kwargs):
        user = self.request.user
        disp_prof = DispatcherProfile.objects.filter(user=user).first()
        queryset = self.get_queryset()

        response_data = []
        seen_businesses = set()
        for order in queryset:
            business = order.user_business
            collected_orders_count = business.orders_user.filter(
                pursuit='waiting for collection',
                # pickup_date=self.today_jalali,
                dispatcher_sender=disp_prof
            ).aggregate(total_count=Sum('count'))['total_count'] or 0  # اگر مقدار None باشد، 0 قرار می‌دهد

            if business.id not in seen_businesses:
                response_data.append({
                    'business_id': business.id,
                    'business_name': business.name,
                    'count_of_package': collected_orders_count,
                })
                seen_businesses.add(business.id)

        return Response(response_data, status=status.HTTP_200_OK)
    

class DispBussinessCollectedOrders(generics.ListAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    # @property
    # def today_jalali(self):
    #     """ مقدار تاریخ امروز به صورت جلالی و به شکل متن """
    #     today = datetime.date.today()
    #     return english_to_persian_number(str(date2jalali(today)).replace('-', '/'))

    def get_queryset(self):
        user = self.request.user
        # بررسی وجود user.profile
        # if not hasattr(user, 'profile'):
        #     return Business.objects.none()
        # # دریافت تمام بیزینس‌هایی که سفیر با آنها کار می‌کند
        # businesses = Business.objects.filter(dispatcherprofile__user=user)
        # # فیلتر کردن بیزینس‌هایی که امروز سفارشی با وضعیت "جمع‌آوری شده" دارند
        # collected_businesses = businesses.filter(
        #     orders_user__pursuit='collected',
        #     orders_user__pickup_date=self.today_jalali  # استفاده از متد today_jalali
        # ).distinct()
        disp_prof = DispatcherProfile.objects.filter(user=user).first()
        orders = Order.objects.filter(
            # pickup_date=self.today_jalali,
            dispatcher_sender=disp_prof,
            pursuit='collected'
        )

        return orders

    def list(self, request, *args, **kwargs):
        user = self.request.user
        disp_prof = DispatcherProfile.objects.filter(user=user).first()
        queryset = self.get_queryset()
        # بررسی اینکه آیا داده‌ای وجود دارد
        # if not queryset.exists():
        #     return Response({"message": "هیچ سفارش جمع‌آوری‌شده‌ای پیدا نشد"}, status=status.HTTP_404_NOT_FOUND)

        response_data = []
        seen_businesses = set()
        for order in queryset:
            business = order.user_business
            collected_orders_count = business.orders_user.filter(
                pursuit='collected',
                # pickup_date=self.today_jalali,
                dispatcher_sender=disp_prof
            ).aggregate(total_count=Sum('count'))['total_count'] or 0  # اگر مقدار None باشد، 0 قرار می‌دهد

            if business.id not in seen_businesses:
                response_data.append({
                    'business_id': business.id,
                    'business_name': business.name,
                    'count_of_package': collected_orders_count,
                })
                seen_businesses.add(business.id)

        return Response(response_data, status=status.HTTP_200_OK)

    

class CollectOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_sender=user.profile, pursuit='waiting for collection', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        tracking_code = self.request.data.get('tracking_code')
        if not tracking_code:
            return Response({'message': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        order = tr_orders.order_by('created_at').last()
        if not tr_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        for order in tr_orders:
            order.pursuit = 'collected'
            order.save()

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)


class DistributOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_sender=user.profile, pursuit='collected', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        tracking_code = self.request.data.get('tracking_code')
        code = self.request.data.get('code')
        if not tracking_code:
            return Response({'message': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not code:
            return Response({'message': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        order = tr_orders.order_by('created_at').last()
        if not tr_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        total_price = tr_orders.order_by('created_at').last().total_price
        val = tr_orders.order_by('created_at').last().value

        wallet_co = IncreaseWalletCo.objects.first()
        # if not wallet_co:
        #     return Response({'message': 'ضریب اعتبار تعریف نشده است'}, status=status.HTTP_404_NOT_FOUND)
        wallet = Wallet.objects.filter(user=user).first()
        
        if not wallet:
            return Response({'message': 'کیف پول وجود ندارد'}, status=status.HTTP_404_NOT_FOUND)
        business = order.user_business
        code_generate_model, created = CodeGenerateModel.objects.get_or_create(
        business=business,
        )
        
        if code_generate_model.code != code:
            return Response({'message': 'کد صحیح نیست'}, status=status.HTTP_404_NOT_FOUND)
        
        for order in tr_orders:
            order.pursuit = 'waiting for distribution'
            order.save()
        #decrease insurance and tax
        val = int(val)
        val_price=0
        if val<1000000 and val>0:
            val_price = 2000
        elif val>=1000000 and val<=20000000:
            val_price = float(val*0.002)
        elif val>20000000 and val<=50000000:
            val_price=float(val*0.003)
        ins_amount = val_price
        # ins_amount = float(val.coefficient*val.max_value*1000000)
        #zarinpal fee
        if float(total_price)*0.01 > 6000:
            decrease_price = 6250
        else:
            decrease_price = float(total_price)*0.01 + 250

        #end of zarinpal fee
        #decrease tax insurance and zarinpal fee
        recieved_price = (float(total_price)/(1+float(tax_co))) - float(decrease_price) - ins_amount

        amount_for_disp = recieved_price*float(sender_disp_co)
        amount_for_disp = round(amount_for_disp)
        wallet.amount += amount_for_disp
        wallet.save()
        sett = SettelmentWallet.objects.create(user=user, tracking_code=tracking_code, amount=amount_for_disp)
        #disp profile
        disp_profs = DispatcherProfile.objects.filter(user=user)
        if disp_profs:
            disp_prof = disp_profs.first()
        else:
            return Response({'message':'پروفایل سفیر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        #end of disp profile

        #find disp bank id in zarinpal
        zarinpal_api = ZarinpalAPI()
        # Fetch bank accounts
        data = zarinpal_api.fetch_bank_accounts()
        bank_accounts = data['data']['BankAccounts']

        disp_bank_id=None
        if bank_accounts:
            for account in bank_accounts:
                if account['iban'] == disp_prof.shaba_number:  # Use dictionary key access
                    disp_bank_id = account['id']  # Access the 'id' key
                    break  # Exit the loop once a match is found
            #end of find bank_account id in zarinpal
            if disp_bank_id is not None:
                # terminal_id = "450513"
                terminal_id = "501449"
                bank_account_id = disp_bank_id
                amount = amount_for_disp*10
                description = 'پرداخت پورسانت رای پیک'
                reconciliation_parts = 'MULTI'

                
                # call zarinpal payout url 
                zarinpal_api = ZarinpalAPI()

                # Call the payout_add method
                result = zarinpal_api.payout_add(
                    terminal_id=terminal_id,
                    bank_account_id=bank_account_id,
                    amount=amount,
                    description=description,
                    reconciliation_parts=reconciliation_parts
                )
                # Handle the response
                if result is None or "error" in result:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت تحویل شد", 
                    }, status=status.HTTP_200_OK)                    
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("error", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_412_PRECONDITION_FAILED)

                # Check if the response contains the expected data
                if "data" in result and "resource" in result["data"]:
                    sett.settlement = True
                    sett.save()
                    return Response({
                        "message": "با موفقیت تحویل شد", 
                    }, status=status.HTTP_200_OK)
                else:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت تحویل شد", 
                    }, status=status.HTTP_200_OK)
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("errors", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_200_OK)
                #end of zarinpal payout url
            else:
                sett.errormessage = "incorrect shaba number in user profile"
                sett.save()
                return Response({
                    "message": "با موفقیت تحویل شد", 
                }, status=status.HTTP_200_OK)
            #     return Response(
            #     {"message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"},
            #     status=status.HTTP_200_OK
            # )

        else:
            sett.errormessage = "no bank accounts found"
            sett.save()
            return Response({
                "message": "با موفقیت تحویل شد", 
            }, status=status.HTTP_200_OK)
            # return Response(
            #     {"message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"},
            #     status=status.HTTP_200_OK
            # )

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)


class GroupCollectedOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    # @property
    # def today_jalali(self):
    #     """ مقدار تاریخ امروز به صورت جلالی و به شکل متن """
    #     today = datetime.date.today()
    #     return english_to_persian_number(str(date2jalali(today)).replace('-', '/'))

    def get_queryset(self):
        user = self.request.user
        pickup_date = self.request.data.get('pickup_date')
        business_id = self.request.data.get('business_id')
        if not business_id:
            return Response({'message': 'business_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if pickup_date:
            pickup_date= english_to_persian_number(pickup_date)
            business_orders = Order.objects.filter(
                dispatcher_sender=user.profile,
                user_business=business_id, 
                pursuit='waiting for collection', 
                payment_status=True,
                pickup_date=pickup_date,
                )
            return business_orders
        business_orders = Order.objects.filter(
        dispatcher_sender=user.profile,
        user_business=business_id, 
        pursuit='waiting for collection', 
        payment_status=True,
        # pickup_date=self.today_jalali,
        )
        return business_orders
    
    def update(self, request, *args, **kwargs):
        business_orders = self.get_queryset()
        if not business_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        tracking_codes = business_orders.values_list('tracking_code', flat=True).distinct()

        for tracking_code in tracking_codes:
            tr_orders = business_orders.filter(tracking_code=tracking_code)

            if not tr_orders.exists():
                return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
            
            for order in tr_orders:
                order.pursuit = 'collected'
                order.save()

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)
    

class GroupDistributOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    # @property
    # def today_jalali(self):
    #     """ مقدار تاریخ امروز به صورت جلالی و به شکل متن """
    #     today = datetime.date.today()
    #     return english_to_persian_number(str(date2jalali(today)).replace('-', '/'))

    def get_queryset(self):
        user = self.request.user
        business_id = self.request.data.get('business_id')
        if not business_id:
            return Response({'message': 'business_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        business_orders = Order.objects.filter(
            dispatcher_sender=user.profile,
            user_business=business_id, 
            pursuit='collected', 
            payment_status=True,
            # pickup_date=self.today_jalali,
            )
        return business_orders
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')
        if not code:
            return Response({'message': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)
        business_orders = self.get_queryset()
        if not business_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        # لیستی برای ذخیره خطاهای زرین پال
        # failed_tracking_codes = []

        # دریافت لیست یونیک از tracking_code‌های سفارش‌های موجود در business_orders
        tracking_codes = business_orders.values_list('tracking_code', flat=True).distinct()

        for tracking_code in tracking_codes:
            tr_orders = business_orders.filter(tracking_code=tracking_code)
            order = tr_orders.order_by('created_at').last()
            if not tr_orders.exists():
                return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

            total_price = tr_orders.order_by('created_at').last().total_price
            val = tr_orders.order_by('created_at').last().value

            wallet = Wallet.objects.filter(user=user).first()
            
            if not wallet:
                return Response({'message': 'کیف پول وجود ندارد'}, status=status.HTTP_404_NOT_FOUND)
            business = order.user_business
            code_generate_model, created = CodeGenerateModel.objects.get_or_create(
            business=business,
            )
            
            if code_generate_model.code != code:
                return Response({'message': 'کد صحیح نیست'}, status=status.HTTP_404_NOT_FOUND)
            
            for order in tr_orders:
                order.pursuit = 'waiting for distribution'
                order.save()
            
            # کاهش مالیات و بیمه
            val = int(val)
            val_price=0
            if val<1000000 and val>0:
                val_price = 2000
            elif val>=1000000 and val<=20000000:
                val_price = float(val*0.002)
            elif val>20000000 and val<=50000000:
                val_price=float(val*0.003)
            ins_amount = val_price

            if float(total_price)*0.01 > 6000:
                decrease_price = 6250
            else:
                decrease_price = float(total_price)*0.01 + 250

            #end of zarinpal fee
            #decrease tax insurance and zarinpal fee
            recieved_price = (float(total_price)/(1+float(tax_co))) - float(decrease_price) - ins_amount

            amount_for_disp = recieved_price*float(sender_disp_co)
            amount_for_disp = round(amount_for_disp)
            wallet.amount += amount_for_disp
            wallet.save()
            sett = SettelmentWallet.objects.create(user=user, tracking_code=tracking_code, amount=amount_for_disp)
            #disp profile
            disp_profs = DispatcherProfile.objects.filter(user=user)
            if disp_profs:
                disp_prof = disp_profs.first()
            else:
                return Response({'message':'پروفایل سفیر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
            # پیدا کردن شماره حساب در زرین پال
            zarinpal_api = ZarinpalAPI()
            # Fetch bank accounts
            data = zarinpal_api.fetch_bank_accounts()
            bank_accounts = data['data']['BankAccounts']

            disp_bank_id=None
            if bank_accounts:
                for account in bank_accounts:
                    if account['iban'] == disp_prof.shaba_number:  # Use dictionary key access
                        disp_bank_id = account['id']  # Access the 'id' key
                        break  # Exit the loop once a match is found
                #end of find bank_account id in zarinpal
                if disp_bank_id is not None:
                    # terminal_id = "450513"
                    terminal_id = "501449"
                    bank_account_id = disp_bank_id
                    amount = amount_for_disp*10
                    description = 'پرداخت پورسانت رای پیک'
                    reconciliation_parts = 'MULTI'
                   
                    # call zarinpal payout url 
                    zarinpal_api = ZarinpalAPI()

                    # Call the payout_add method
                    result = zarinpal_api.payout_add(
                        terminal_id=terminal_id,
                        bank_account_id=bank_account_id,
                        amount=amount,
                        description=description,
                        reconciliation_parts=reconciliation_parts
                    )
                    # Handle the response
                    if result is None or "error" in result:
                        sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                        sett.save()
                        # failed_tracking_codes.append({"tracking_code": tracking_code,
                        #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                        #     "error": "Failed to add payout", 
                        #     "details": result.get("error", "Unknown error") if result else "Unknown error"
                        # })
                        continue

                    # Check if the response contains the expected data
                    if "data" in result and "resource" in result["data"]:
                        sett.settlement = True
                        sett.save()
                        continue
                    else:
                        sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                        sett.save()
                        # failed_tracking_codes.append({"tracking_code": tracking_code,
                        #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                        #     "error": "Failed to add payout", 
                        #     "details": result.get("errors", "Unknown error") if result else "Unknown error"
                        # })
                        continue
                    #end of zarinpal payout url
                else:
                    sett.errormessage = "incorrect shaba number in user profile"
                    sett.save()
                #     failed_tracking_codes.append({"tracking_code": tracking_code,
                #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"}
                # )

            else:
                sett.errormessage = "no bank accounts found"
                sett.save()
                # failed_tracking_codes.append({"tracking_code": tracking_code,
                #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"}
                # )
        # بررسی وضعیت نهایی و ارسال پاسخ
        # if failed_tracking_codes:
        #     return Response({
        #         "message": "برخی از سفارش‌ها مشکل در پرداخت داشتند",
        #         "failed_orders": failed_tracking_codes
        #     }, status=status.HTTP_412_PRECONDITION_FAILED)

        return Response({
            "message": "با موفقیت تحویل شد", 
            }, status=status.HTTP_200_OK)
    

class RecieveOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_reciever=user.profile, pursuit='waiting for distribution', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        tracking_code = self.request.data.get('tracking_code')
        if not tracking_code:
            return Response({'message': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        order = tr_orders.order_by('created_at').last()
        if not tr_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        for order in tr_orders:
            order.pursuit = 'get by ambassador'
            order.save()
        code = order.delivery_code
        receiver_phone = order.receiver_phone
        receiver_name = order.receiver_name
        business_name = order.user_business.name
        pickup_date = order.pickup_date
        tracking_code = order.tracking_code
        delivery_time = order.service.delivery_time
        delivery_time = transform_time_range(delivery_time)
        receiver_name = receiver_name.replace(' ', '_')
        business_name = business_name.replace(' ', '_')
        SendDeliveryCodeSms(receiver_phone,receiver_name,business_name,tracking_code,delivery_time,code)

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)
    

class GroupRecieveOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        return (
            Order.objects.filter(
                dispatcher_reciever=user.profile,
                pursuit='waiting for distribution',
                payment_status=True
            )
            # .order_by('tracking_code', '-created_at')
            # .distinct('tracking_code')
        )
    
    def update(self, request, *args, **kwargs):
        # tracking_code = self.request.data.get('tracking_code')
        # if not tracking_code:
        #     return Response({'message': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset()
        # tr_orders = orders.filter(tracking_code=tracking_code)
        # order = tr_orders.order_by('created_at').last()
        # if not tr_orders.exists():
        #     return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        tr_list = []
        for order in orders:
            order.pursuit = 'get by ambassador'
            order.save()
            tracking_code = order.tracking_code
            if tracking_code not in tr_list:
                code = order.delivery_code
                receiver_phone = order.receiver_phone
                receiver_name = order.receiver_name
                business_name = order.user_business.name
                pickup_date = order.pickup_date
                delivery_time = order.service.delivery_time
                delivery_time = transform_time_range(delivery_time)
                receiver_name = receiver_name.replace(' ', '_')
                business_name = business_name.replace(' ', '_')
                SendDeliveryCodeSms(receiver_phone,receiver_name,business_name,tracking_code,delivery_time,code)
            tr_list.append(tracking_code)

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)


class RevokeOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_sender=user.profile, pursuit='waiting for collection', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        tracking_code = self.request.POST.get('tracking_code')
        if not tracking_code:
            return Response({'message': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        if not tr_orders.exists():
            return Response({'message': 'سفارش یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        for order in tr_orders:
            sender_phone = order.sender_phone
            sender_name = order.sender_name
            sender_name = sender_name.replace(' ','_')
            buisiness_name = order.user_business.name
            buisiness_name = buisiness_name.replace(' ','_')
            pickup_date = order.pickup_date
            pickup_time = order.service.pickup_time
            pickup_time = transform_time_range(pickup_time)
            order.pursuit = 'revoke'
            order.save()

        SendCancelOrderSms(sender_phone, sender_name, buisiness_name, pickup_date, pickup_time)

        return Response({'message': 'با موفقیت انجام شد'}, status=status.HTTP_202_ACCEPTED)


class DeliverOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_reciever=user.profile, pursuit='get by ambassador', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        tracking_code = self.request.data.get('tracking_code')
        code = self.request.data.get('delivery_code')
        if not tracking_code:
            return Response({'error': 'Tracking code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        if not tr_orders.exists():
            return Response({'message': 'کد رهگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        tr_orders = orders.filter(tracking_code=tracking_code, delivery_code=code)
        if not tr_orders.exists():
            return Response({'message': 'کد تحویل اشتباه است'}, status=status.HTTP_404_NOT_FOUND)
        
        total_price = tr_orders.order_by('created_at').last().total_price

        wallet_co = IncreaseWalletCo.objects.first()
        if not wallet_co:
            return Response({'message': 'ضریب اعتبار تعریف نشده است'}, status=status.HTTP_404_NOT_FOUND)
        wallet = Wallet.objects.filter(user=user).first()
        if not wallet:
            return Response({'message': 'کیف پول وجود ندارد'}, status=status.HTTP_404_NOT_FOUND)
        last_order = tr_orders.order_by('created_at').last()
        val = last_order.value
        #decrease insurance and tax
        val = int(val)
        val_price=0
        if val<1000000 and val>0:
            val_price = 2000
        elif val>=1000000 and val<=20000000:
            val_price = float(val*0.002)
        elif val>20000000 and val<=50000000:
            val_price=float(val*0.003)
        ins_amount = val_price
        # ins_amount = float(val.coefficient*val.max_value*1000000)

        for order in tr_orders:
            order.pursuit = 'delivered'
            order.save()
        #zarinpal fee
        if float(total_price)*0.01 > 6000:
            decrease_price = 6250
        else:
            decrease_price = float(total_price)*0.01 + 250

        #end of zarinpal fee
        recieved_price = (float(total_price)/(1+float(tax_co))) - float(decrease_price) - ins_amount

        amount_for_disp = recieved_price*float(receiver_disp_co)
        amount_for_disp = round(amount_for_disp)
        wallet.amount += amount_for_disp
        wallet.save()
        sett = SettelmentWallet.objects.create(user=user, tracking_code=tracking_code, amount=amount_for_disp)
        #disp profile
        disp_profs = DispatcherProfile.objects.filter(user=user)
        if disp_profs:
            disp_prof = disp_profs.first()
        else:
            return Response({'message':'پروفایل سفیر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        #end of disp profile

        #find disp bank id in zarinpal
        zarinpal_api = ZarinpalAPI()
        # Fetch bank accounts
        data = zarinpal_api.fetch_bank_accounts()
        bank_accounts = data['data']['BankAccounts']

        disp_bank_id=None
        if bank_accounts:
            for account in bank_accounts:
                if account['iban'] == disp_prof.shaba_number:  # Use dictionary key access
                    disp_bank_id = account['id']  # Access the 'id' key
                    break  # Exit the loop once a match is found
            
            if disp_bank_id is not None:
                # terminal_id = "450513"
                terminal_id = "501449"
                bank_account_id = disp_bank_id
                amount = amount_for_disp*10
                description = 'پرداخت پورسانت رای پیک'
                reconciliation_parts = 'MULTI'

                
                # Initialize the Zarinpal API class with your token
                zarinpal_api = ZarinpalAPI()

                # Call the payout_add method
                result = zarinpal_api.payout_add(
                    terminal_id=terminal_id,
                    bank_account_id=bank_account_id,
                    amount=amount,
                    description=description,
                    reconciliation_parts=reconciliation_parts
                )
                # Handle the response
                if result is None or "error" in result:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت تحویل شد", 
                        }, status=status.HTTP_200_OK)
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت لطفا با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("error", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_412_PRECONDITION_FAILED)

                # Check if the response contains the expected data
                if "data" in result and "resource" in result["data"]:
                    sett.settlement = True
                    sett.save()
                    return Response({
                        "message": "با موفقیت افزوده شد", 
                    }, status=status.HTTP_200_OK)
                else:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت تحویل شد", 
                        }, status=status.HTTP_200_OK)
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت لطفا با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("errors", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_412_PRECONDITION_FAILED)
            else:
                sett.errormessage = "incorrect shaba number in user profile"
                sett.save()
                return Response({
                    "message": "با موفقیت تحویل شد", 
                    }, status=status.HTTP_200_OK)
                # return Response(
                #     {'message': 'جهت تسویه به شماره کارت لطفا با پشتیبانی تماس بگیرید'},
                #     status=status.HTTP_412_PRECONDITION_FAILED
                # )
        else:
            sett.errormessage = "no bank accounts found"
            sett.save()
            return Response({
                "message": "با موفقیت تحویل شد", 
                }, status=status.HTTP_200_OK)
            # return Response(
            #     {'message': 'جهت تسویه به شماره کارت لطفا با پشتیبانی تماس بگیرید'},
            #     status=status.HTTP_412_PRECONDITION_FAILED
            # )


class ReturnOrderCodeView(APIView):
    def post(self, request):
        user = self.request.user
        tracking_code = request.POST.get('tracking_code')
        orders = Order.objects.filter(dispatcher_reciever=user.profile, 
                                      pursuit='get by ambassador', 
                                      tracking_code=tracking_code,
                                      payment_status=True)
        if not orders.exists():
            return Response({'message': 'سفارشی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        return_code = random.randint(1000, 9999)
        for order in orders:
            sender_phone = order.sender_phone
            sender_name = order.sender_name
            sender_name = sender_name.replace(' ', '_')
            receiver_name = order.receiver_name
            receiver_name = receiver_name.replace(' ', '_')
            pickup_date = order.pickup_date
            #create new code for return
            order.delivery_code = return_code
            order.save()
        
        SendReturnCode(sender_phone, sender_name, receiver_name, pickup_date, return_code)

        return Response({'message': 'پیام با موفقیت ارسال شد'}, status=status.HTTP_200_OK)


class ReturnOrderView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticatedWithToken]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.filter(dispatcher_reciever=user.profile, pursuit='get by ambassador', payment_status=True)
        return orders
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        tracking_code = self.request.data.get('tracking_code')
        return_code = self.request.data.get('return_code')
        if not tracking_code:
            return Response({'message': 'کد رهگیری یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not return_code:
            return Response({'message': 'کد استرداد یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        orders = self.get_queryset()
        tr_orders = orders.filter(tracking_code=tracking_code)
        if not tr_orders.exists():
            return Response({'message': 'سفارش برای کد رهگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        tr_orders = orders.filter(tracking_code=tracking_code, delivery_code=return_code)
        if not tr_orders.exists():
            return Response({'message': 'کد مرجوعی اشتباه است '}, status=status.HTTP_404_NOT_FOUND)
        total_price = tr_orders.order_by('created_at').last().total_price

        wallet_co = IncreaseWalletCo.objects.first()
        if not wallet_co:
            return Response({'message': 'ضریب اعتبار تعریف نشده است'}, status=status.HTTP_404_NOT_FOUND)
        wallet = Wallet.objects.filter(user=user).first()
        if not wallet:
            return Response({'message': 'کیف پول وجود ندارد'}, status=status.HTTP_404_NOT_FOUND)
        val = tr_orders.order_by('created_at').last().value
        for order in tr_orders:
            order.pursuit = 'returned'
            order.save()
        #decrease insurance and tax
        val = int(val)
        val_price=0
        if val<1000000 and val>0:
            val_price = 2000
        elif val>=1000000 and val<=20000000:
            val_price = float(val*0.002)
        elif val>20000000 and val<=50000000:
            val_price=float(val*0.003)
        ins_amount = val_price
        # ins_amount = float(val.coefficient*val.max_value*1000000)
        #zarinpal fee
        if float(total_price)*0.01 > 6000:
            decrease_price = 6250
        else:
            decrease_price = float(total_price)*0.01 + 250

        #end of zarinpal fee
        #decrease tax insurance and zarinpal fee
        recieved_price = (float(total_price)/(1+float(tax_co))) - float(decrease_price) - ins_amount

        amount_for_disp = recieved_price*float(receiver_disp_co)
        amount_for_disp = round(amount_for_disp)
        wallet.amount += amount_for_disp
        wallet.save()
        sett = SettelmentWallet.objects.create(user=user, tracking_code=tracking_code, amount=amount_for_disp)
        #disp profile
        disp_profs = DispatcherProfile.objects.filter(user=user)
        if disp_profs:
            disp_prof = disp_profs.first()
        else:
            return Response({'message':'پروفایل سفیر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        #end of disp profile

        #find disp bank id in zarinpal
        zarinpal_api = ZarinpalAPI()
        # Fetch bank accounts
        data = zarinpal_api.fetch_bank_accounts()
        bank_accounts = data['data']['BankAccounts']

        disp_bank_id=None
        if bank_accounts:
            for account in bank_accounts:
                if account['iban'] == disp_prof.shaba_number:  # Use dictionary key access
                    disp_bank_id = account['id']  # Access the 'id' key
                    break  # Exit the loop once a match is found
            #end of find bank_account id in zarinpal
            if disp_bank_id is not None:
                # terminal_id = "450513"
                terminal_id = "501449"
                bank_account_id = disp_bank_id
                amount = amount_for_disp*10
                description = 'پرداخت پورسانت رای پیک'
                reconciliation_parts = 'MULTI'

                
                # call zarinpal payout url 
                zarinpal_api = ZarinpalAPI()

                # Call the payout_add method
                result = zarinpal_api.payout_add(
                    terminal_id=terminal_id,
                    bank_account_id=bank_account_id,
                    amount=amount,
                    description=description,
                    reconciliation_parts=reconciliation_parts
                )
                # Handle the response
                if result is None or "error" in result:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت مرجوع شد", 
                        }, status=status.HTTP_200_OK)                    
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("error", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_412_PRECONDITION_FAILED)

                # Check if the response contains the expected data
                if "data" in result and "resource" in result["data"]:
                    sett.settlement = True
                    sett.save()
                    return Response({
                        "message": "با موفقیت مرجوع شد", 
                    }, status=status.HTTP_200_OK)
                else:
                    sett.errormessage = result.get("error", "Unknown error") if result else "Unknown error"
                    sett.save()
                    return Response({
                        "message": "با موفقیت مرجوع شد", 
                        }, status=status.HTTP_200_OK)
                    # return Response({
                    #     "message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید",
                    #     "error": "Failed to add payout", 
                    #     "details": result.get("errors", "Unknown error") if result else "Unknown error"
                    # }, status=status.HTTP_412_PRECONDITION_FAILED)
                #end of zarinpal payout url
            else:
                sett.errormessage = "incorrect shaba number in user profile"
                sett.save()
                return Response({
                    "message": "با موفقیت مرجوع شد", 
                    }, status=status.HTTP_200_OK)
            #     return Response(
            #     {"message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"},
            #     status=status.HTTP_412_PRECONDITION_FAILED
            # )

        else:
            sett.errormessage = "no bank accounts found"
            sett.save()
            return Response({
                "message": "با موفقیت مرجوع شد", 
                }, status=status.HTTP_200_OK)
            # return Response(
            #     {"message": "جهت تسویه به شماره کارت با پشتیبانی تماس بگیرید"},
            #     status=status.HTTP_412_PRECONDITION_FAILED
            # )
        

class ResendCodeView(APIView):
    def post(self, request):
        user = self.request.user
        tracking_code = request.POST.get('tracking_code')
        orders = Order.objects.filter(dispatcher_reciever=user.profile, 
                                      pursuit='get by ambassador', 
                                      tracking_code=tracking_code,
                                      payment_status=True)
        order = orders.last()
        code = order.delivery_code
        receiver_phone = order.receiver_phone
        receiver_name = order.receiver_name
        business_name = order.user_business.name
        pickup_date = order.pickup_date
        tracking_code = order.tracking_code
        delivery_time = order.service.delivery_time
        delivery_time = transform_time_range(delivery_time)
        receiver_name = receiver_name.replace(' ', '_')
        business_name = business_name.replace(' ', '_')
        SendDeliveryCodeSms(receiver_phone,receiver_name,business_name,tracking_code,delivery_time,code)

        return Response({'message': 'پیام با موفقیت ارسال شد'}, status=status.HTTP_200_OK)