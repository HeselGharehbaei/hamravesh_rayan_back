import requests
from django.utils.translation import gettext as _
from django.shortcuts import  get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
from config.settings import API_KEY
from business.models import Business
from payment.models import IncreaseWalletCo, Wallet,PaymentAmount
from .api_serializers import *
from options.api_serializers import ServiceSerializers
from apikey.models import ApiKeyModel
from django.db.models import Sum, Case, When, IntegerField, F
from config.settings import EMAIL_HOST_USER
from django.core.mail import send_mail


def sendCancelSmsC(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'template': 'cancelorderycust'
    }
    res = requests.post(url, data)


class OrderCreateView(APIView):

    def post(self, request, *args, **kwargs):

                # Get the API key from the request data
        key = self.request.headers.get('apikey')
        if not key:
            return Response({'message': 'apikey ارسال نشده است'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if the API key exists in the database
            apikey = ApiKeyModel.objects.filter(key=key).first()
            if not apikey:
                return Response({'message': 'API key نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the business ID associated with the API key
            bus_id = apikey.business.id
            get_message = apikey.get_message
        except Exception as e:
            # If there is an error, return a bad request with the error message
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch the business associated with the business ID
        business = Business.objects.filter(id=bus_id).first()

        # If no business is found, return an error message
        if not business:
            return Response({'message': 'کسب و کار یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        if business.real_profile:
            user = business.real_profile.user  # دسترسی به user از real_profile
        elif business.legal_profile:
            user =business.legal_profile.user_admin  # دسترسی به user از legal_profile   
        else:
            raise serializers.ValidationError('کسب و کار فاقد پروفایل است')         
        # گرفتن داده‌های ورودی از درخواست
        serializer = OrderSerializer(data=request.data, context={'request': request, 'business': business, 'get_message': get_message, 'user': user, 'view': self})


        if serializer.is_valid():
            # ایجاد اوردرها و گرفتن تعداد کل جعبه‌ها
            result = serializer.validated_data
            total_box_count = result["total_box_count"]
            tracking_code= result["tracking_code"]

            if get_message:
                # ارسال پیامک یا ایمیل به کاربر پس از ثبت موفقیت‌آمیز
                if user.phone is not None:
                    SendApiOrderSms(f'{user.phone}', tracking_code)
                elif user.email is not None:
                    subject = 'ثبت سفارش در رایان'
                    message = f'سفارش شما با موفقیت در رایان ثبت شد. کد رهگیری سفارش: {tracking_code}'

                    from_email = EMAIL_HOST_USER  # ایمیل فرستنده
                    to_email = user.email

                    send_mail(subject, message, from_email, [to_email])

            # بازگشت پاسخ موفقیت‌آمیز به همراه داده‌های اوردرها
            return Response({
                'message': 'سفارش شما با موفقیت ثبت شدند.',
                'tracking_code': tracking_code,  # حالا orders بارگذاری شده شامل tracking_code
                'total_box_count': total_box_count  # ارسال تعداد کل جعبه‌ها
            }, status=status.HTTP_201_CREATED)

        else:
            # اگر داده‌ها معتبر نباشند، پاسخ خطا می‌دهیم.
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrackingOrderView(APIView):
    """
    View to display order information using tracking_code from a POST request
    """
    def post(self, request):
        # Check API Key in the header and is valid
        key = request.headers.get('apikey')
        if not key:
            return Response({'message': 'apikey ارسال نشده است'}, status=status.HTTP_400_BAD_REQUEST)
        apikey = ApiKeyModel.objects.filter(key=key).first()
        if not apikey:
            return Response({'message': f'API key نامعتبر است: {key}'}, status=status.HTTP_400_BAD_REQUEST)      

        # Retrieve tracking_code from the request body
        tracking_code = request.data.get('tracking_code')
        if not tracking_code:
            return Response({'message': 'کد رهگیری الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve orders with matching tracking_code
        orders = Order.objects.filter(tracking_code=tracking_code)
        if not orders.exists():
            return Response({'message': 'هیچ سفارشی با این کد رهگیری یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        # Group and aggregate the count of packages by size
        grouped_orders = orders.values('tracking_code').annotate(
            small_size_count=Sum(
                Case(
                    When(size__title='کوچک', then=F('count')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            medium_size_count=Sum(
                Case(
                    When(size__title='متوسط', then=F('count')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            big_size_count=Sum(
                Case(
                    When(size__title='بزرگ', then=F('count')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
        )

        # Prepare response data
        response_data = {
            'tracking_code': tracking_code,
            'order': [],
        }

        # Aggregate order details for each distinct tracking_code
        for order in orders:
            service_serializer = ServiceSerializers(order.service)

            # Find the aggregated data for this specific tracking_code
            order_group = next((item for item in grouped_orders if item['tracking_code'] == order.tracking_code), None)

            if order_group:
                small_size_count = order_group.get('small_size_count', 0)
                medium_size_count = order_group.get('medium_size_count', 0)
                big_size_count = order_group.get('big_size_count', 0)
            else:
                small_size_count = medium_size_count = big_size_count = 0

            # Append order details with aggregated package counts
            response_data['order'].append({
                'tracking_code': order.tracking_code,
                'sender_name': order.sender_name,
                'sender_address': order.sender_address,
                'receiver_name': order.receiver_name,
                'receiver_address': order.receiver_address,
                'pickup_date': order.pickup_date,
                'total_price': order.total_price,
                'status': order.pursuit,
                'small_size_count': small_size_count,
                'medium_size_count': medium_size_count,
                'big_size_count': big_size_count,
                'order_number': order.order_number,
                'order_description': order.order_description,
                'address_description': order.address_description,
                'content': order.content.title if order.content else None,
                'service': order.service.title if order.service else None,
                'service_description': service_serializer.data['description'],
                'value': order.value,
                'pickup_date': order.pickup_date,
                'sender_title': order.sender_title,
                'sender_address': order.sender_address,
                'receiver_name': order.receiver_name,
                'receiver_address': order.receiver_address,
                'sender_map_link': order.sender_map_link,
                'receiver_map_link': order.receiver_map_link,
                'total_price': order.total_price,
                'status': order.pursuit,
                # 'dispatcher_sender': order.dispatcher_sender.user.username if order.dispatcher_sender.user.username else None,
                # 'dispatcher_receiver': order.dispatcher_reciever.user.username if order.dispatcher_reciever.user.username else None,
            })

        return Response(response_data['order'][0], status=status.HTTP_200_OK)


class CancelOrderView(generics.UpdateAPIView):
    serializer_class = OrderSerializer

    def validate_api_key(self, key):
        if not key:
            return Response({'message': _('apikey ارسال نشده است')})
        
        apikey = ApiKeyModel.objects.filter(key=key).select_related('business').first()
        if not apikey:
            return Response({'message': _('API key نامعتبر است')})
        
        return apikey.business, apikey.get_message

    def get_user_from_business(self, business):
        if business.real_profile:
            return business.real_profile.user
        elif business.legal_profile:
            return business.legal_profile.user_admin
        else:
            return Response({'message': _('کسب و کار فاقد پروفایل است')})
        
    def update(self, request, *args, **kwargs):
        key = request.headers.get('apikey')
        business,get_message = self.validate_api_key(key)
        user = self.get_user_from_business(business)
        tracking_code = request.data.get('tracking_code')
        orders = Order.objects.filter(
            user_business_id=business.id,
            tracking_code=tracking_code,
            pursuit__in=['waiting for payment', 'waiting for collection']
        ).order_by('tracking_code')

        if not orders.exists():
            return Response({'message': _('سفارش یافت نشد')}, status=status.HTTP_404_NOT_FOUND)

        total_price = orders.last().total_price
        tracking_code = orders.last().tracking_code 
        decrease_price = self.calculate_decrease_price(user, tracking_code, total_price)
        received_price = total_price - decrease_price

        waiting_collection_status = orders.last().pursuit == 'waiting for collection'
        for order in orders:
            order.pursuit = 'canceled'
            order.payment_status = False
            order.dispatcher_reciever = None
            order.dispatcher_sender = None
            order.save()
        if waiting_collection_status:
            wallet = Wallet.objects.filter(user=user).first()
            wallet.amount += received_price
            wallet.save()

            PaymentAmount.objects.create(
                user=user,
                amount=received_price,
                tracking_code=tracking_code,
                authority='canceled order',
                payment_status='deposit to wallet',
                deposit=False
            )
            
            last_order = orders.last() or orders.first()
            check_service_count = CheckServiceCount.objects.filter(
                pickup_date=last_order.pickup_date,
                service_type=last_order.service.s_type,
                service_title=last_order.service.title
            ).first()
            check_service_count.service_count += 1
            check_service_count.save()

        self.send_cancel_sms(get_message, user, tracking_code)

        return Response({'message': _('با موفقیت تغییر یافت')}, status=status.HTTP_200_OK)

    def calculate_decrease_price(self, user, tracking_code, total_price):
        if PaymentAmount.objects.filter(user=user, tracking_code__contains=tracking_code, deposit=True).exists():
            return max(total_price * 0.01 + 250, 6250)
        wallet_co = get_object_or_404(IncreaseWalletCo)
        return total_price * float(wallet_co.Coefficient)

    def send_cancel_sms(self, get_message, user, tracking_code):
        if '@' not in user.username and get_message:  # Assuming username is phone for SMS
            try:
                sendCancelSmsC(user.username, tracking_code)
            except Exception:
                pass
