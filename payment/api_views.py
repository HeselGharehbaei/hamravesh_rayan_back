import ast
import random
from django.core.mail import send_mail
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from persiantools.jdatetime import JalaliDate

import datetime
import requests
import json
import re
import jdatetime
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from config import settings
from dispatcher_profile.models import DispatcherProfile
# from options.models import Value
from order.models import Order
from datetime import date
from config.settings import API_KEY
from core.utils.constant import f_site as site, site as siteb
from payment.models import Wallet, CreditCo, Credit, PaymentAmount, IncreaseWalletCo
from usermodel.models import CustomUser
from userprofile.models import LegalUserProfile, RealUserProfile
from prices.views import can_fit
from options.models import CheckServiceCount
# from dispatcher_payment.views import allocation2
from cities.tests import district_list
import logging

logging.basicConfig(
    filename='function_logs.log',  # Log file name
    level=logging.DEBUG,          # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date and time format
)

file_handler = logging.FileHandler('function_logs.log')
file_handler.setLevel(logging.DEBUG)  # File logging level
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Create a console handler for logging to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Console logging level
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add handlers to the root logger
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(console_handler)


MERCHANT = f'63c90357-1d58-4aae-8372-5cc9a360e2e2'
ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/{authority}"

# amount = 11000  # Rial / Required
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"  # Required
# Important: need to edit for realy server.
CallbackURL = f'{siteb}/payment/verify/order/'
CallbackURL_wallet = f'{siteb}/payment/verify/wallet/'  # ALLOWED_HOSTS[0]
#saman
saman_api_token = "https://sep.shaparak.ir/onlinepg/onlinepg"
CallbackURLSaman = f'{siteb}/payment/saman/verify/order/'
CallbackURL_walletSaman = f'{siteb}/payment/saman/verify/wallet/'  # ALLOWED_HOSTS[0]
Terminal_id_saman = "14680627"

def english_to_persian_number(english_str):
    # Define a mapping from English digits to Persian digits
    english_to_persian_map = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }

    # Replace each English digit with the corresponding Persian digit
    persian_str = ''.join(english_to_persian_map.get(char, char) for char in english_str)
    return persian_str

def is_thursday(jalali_date_str):
    """
    Check if a given Jalali date is Thursday.
    
    :param jalali_date_str: Date in 'YYYY/MM/DD' format (Jalali)
    :return: Boolean (True if Thursday, False otherwise)
    """
    try:
        # Parse the Jalali date string manually
        year, month, day = map(int, jalali_date_str.split('/'))
        jalali_date = JalaliDate(year, month, day)
        
        # Convert to Gregorian date to check the weekday
        gregorian_date = jalali_date.to_gregorian()
        
        # Check if the Gregorian weekday corresponds to Thursday (3 is Thursday in Python)
        return gregorian_date.weekday() == 3
    except Exception as e:
        return False

def SendOrderSms(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        # 'token2': token2,
        'template': 'TrackingCode'
    }
    res = requests.post(url, data)


def SendOrderMultiSms(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        # 'token2': token2,
        'template': 'OrderMulti'
    }
    res = requests.post(url, data)

def SendFreeDispatcher(receptor, token, token2, token3, token20):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        'token2': token2,
        'token3': token3,
        'token20': token20,
        'template': 'freedispatcher'
    }
    res = requests.post(url, data)

def transform_time_range(input_str):
    # Define the regex pattern to extract hours from the input string
    pattern = r'از ساعت (\d+):\d+ تا ساعت (\d+):\d+'
    # 'از ساعت (\d+):\d+ تا ساعت (\d+):\d+'
    
    # Search for the pattern in the input string
    match = re.search(pattern, input_str)
    
    if match:
        # Extract the hours from the match groups
        start_hour = match.group(1)
        end_hour = match.group(2)
        
        # Format the result as required
        result = f"{start_hour}الی{end_hour}"
        return result
    else:
        # Return None or an appropriate message if the pattern does not match
        return "Pattern not found"



@csrf_exempt
# @api_view()
def send_request_order(request):
    global amount
    user_id = request.GET.get('id')
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return redirect(f'{site}/order/payment')
    bus_id = request.GET.get('bus_id')
    real = RealUserProfile.objects.filter(user=user).first()
    legal = LegalUserProfile.objects.filter(user_admin=user).first()
    user_phone = None
    user_email = None
    if user.phone is not None:
        user_phone = user.phone
    else:
        user_email = user.email

    if legal:
        orders = Order.objects.filter(user_business__legal_profile=legal,
                                      user_business__id=bus_id,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                      )
        if not orders.exists():
            return HttpResponse('Order not found', status=404)
    elif real:
        orders = Order.objects.filter(user_business__real_profile=real,
                                      user_business_id=bus_id,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                         )
        if not orders.exists():
            return HttpResponse('Order not found', status=404)

    else:
        return redirect(f'{site}/order/payment')
    current_time = datetime.datetime.now()
    current_date = current_time.date()
    current_jalali_date = str(jdatetime.date.fromgregorian(date=current_date))
    pickup_date= orders.first().pickup_date 
    service_time= orders.first().service.hour
    current_j_persian_date = english_to_persian_number(current_jalali_date.replace('-', '/'))
    if current_j_persian_date == pickup_date:
        if current_time.time() > service_time:
            return HttpResponse({'message':'زمان ثبت سفارش برای این سرویس در روز جاری به پایان رسیده است'}, status=status.HTTP_400_BAD_REQUEST)
        
    # if orders.first().service.title == 'سرویس درون شهری - عصرگاهی':
    #     if is_thursday(pickup_date):
    #         return HttpResponse({'message':'این سرویس در روزهای پنجشنبه فعال نیست'}, status=status.HTTP_404_NOT_FOUND)    
    tracking_codes = set()
    for order in orders:
        tracking_codes.add(order.tracking_code)

    #check the count of service and box
    amount = 0
    for tracking_code in tracking_codes:
        orders = Order.objects.filter(tracking_code=tracking_code).all()
        n1= n2= n3= 0
        last_order = orders.order_by('created_at').last()
        for order in orders:
            if order.size.title == 'بزرگ':
                n1 += int(order.count)
            elif order.size.title == 'متوسط':
                n2 += int(order.count)
            elif order.size.title == 'کوچک':
                n3 += int(order.count)    
        # if can_fit(n1, n2, n3):
        pickup_date= last_order.pickup_date
        service_type= last_order.service.s_type
        service_title= last_order.service.title
        service_count= last_order.service.count
        check_service_count= CheckServiceCount.objects.filter(
            pickup_date=pickup_date, 
            service_type=service_type, 
            service_title=service_title).first()
        if check_service_count:
            if check_service_count.service_count<len(tracking_codes) or service_count<len(tracking_codes):
                return HttpResponse('متاسفانه سرویسی برای این تاریخ وجود ندارد', status=404)
        # else:
        #     return HttpResponse('تعداد بسته‌های انتخابی بیش از حد مجاز است', status=404) 
        #check disp for this zone
        disp = last_order.dispatcher_sender
        zone = last_order.receiver_zone
        service = last_order.service
                    
        # if disp is not None:
        #     return HttpResponse('سفارش از قبل تخصیص داده شده', status=status.HTTP_400_BAD_REQUEST)
        
        # dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id)
        
        # if not dispatchers_in_this_zone.exists():
        #     return HttpResponse(f'سفیری در این منطقه یافت نشد  {zone}.', status=status.HTTP_404_NOT_FOUND)
        
        amount += (last_order.total_price*10)
    
    req_data = {
            "merchant_id": MERCHANT,
            "amount": amount,
            "callback_url": CallbackURL,
            "description": description,
            # "metadata": {"mobile": "", "email": ""}
        }

    req_header = {"accept": "application/json", "content-type": "application/json'"}
    req = requests.post(url=ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)
    if len(req.json()['errors']) == 0:
        authority = req.json()['data']['authority']
        PaymentAmount.objects.create(user=user, amount=amount, tracking_code=tracking_codes, authority=authority)
        return redirect(ZP_API_STARTPAY.format(authority=authority))
    else:
        e_code = req.json()['errors']['code']
        e_message = req.json()['errors']['message']
        return HttpResponse(f"Error code: {e_code}, Error Message: {e_message}") 
    

def verify_order(request):
    authority = request.GET['Authority']
    paied = PaymentAmount.objects.filter(authority=authority).first()
    if paied:
        tracking_code = ast.literal_eval(paied.tracking_code)
        tracking_codes = list(tracking_code)
        user = paied.user
        amount = paied.amount
        paied.date = datetime.datetime.now()
        paied.save()
    else:
        return redirect(f'{site}/order/payment/failed')
    real = RealUserProfile.objects.filter(user=user).first()
    legal = LegalUserProfile.objects.filter(user_admin=user).first()
    user_phone = None
    user_email = None
    if user.phone is not None:
        user_phone = user.phone
    else:
        user_email = user.email
    
    if legal:
        orders = Order.objects.filter(user_business__legal_profile=legal, 
                                      tracking_code__in=tracking_codes,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                      )
        order_number = orders.last().order_number
        if not orders.exists():
            return HttpResponse('خطایی مربوط به پروفایل یا کدرهگیری رخ داده', status=404)
    elif real:
        orders = Order.objects.filter(user_business__real_profile=real,
                                        tracking_code__in=tracking_codes,
                                        payment_status=False,
                                        pursuit='waiting for payment'
                                        )
        order_number = orders.last().order_number
        if not orders.exists():
            return HttpResponse('خطایی مربوط به پروفایل یا کدرهگیری رخ داده', status=406)
    else:
        return redirect(f'{site}/order/payment')
    t_status = request.GET.get('Status')
    t_authority = request.GET.get('Authority')
    if request.GET.get('Status') == 'OK':
        req_header = {"accept": "application/json", "content-type": "application/json'"}
        req_data = {
            "merchant_id": MERCHANT,
            "amount": amount,
            "authority": t_authority,
        }
        req = requests.post(url=ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)
        if len(req.json()['errors']) == 0:
            t_status = req.json()['data']['code']

            if t_status == 100:

                paied.payment_status = True
                paied.save()
                # #increase wallet charge for every payment
                
                # wallet_co = get_object_or_404(
                #     IncreaseWalletCo
                # )
                # wallet = get_object_or_404(
                #     Wallet,
                #     user=user
                # )
                # coefficient = float(wallet_co.Coefficient)
                # wallet.amount += amount/10*coefficient
                # wallet.save()
                # this flag check if order has not been payed credit
                for tracking_code in tracking_codes:
                    orders = Order.objects.filter(tracking_code=tracking_code)
                    orders_count=len(orders)
                    flag = True
                    pickup_date = orders.first().pickup_date
                    for order in orders:
                        order.payment_status = True
                        order.bank_code = req.json()['data']['ref_id']
                        order.payment = 'Transaction success'
                        order.pursuit = 'waiting for collection'
                        if order.credit == True:
                            flag = False
                        order.credit = True
                        order.save()
                        # credit add
                        # value_id = order.value.id
                    paid_orders= Order.objects.filter(
                        tracking_code=tracking_code, 
                        payment_status = True
                        ) 
                    
                    #count service numbers for 
                    if paid_orders.count() == orders_count:
                        service_type = paid_orders.first().service.s_type
                        service_title = paid_orders.first().service.title  
                        service_count = paid_orders.first().service.count 
                        pickup_date= paid_orders.first().pickup_date
                        check_service_count= CheckServiceCount.objects.filter(
                        pickup_date=pickup_date, 
                        service_type=service_type, 
                        service_title=service_title).first() 
                        if check_service_count: 
                            check_service_count.service_count-=1 
                            check_service_count.save() 
                        elif not check_service_count:   
                            check_service_count= CheckServiceCount.objects.create(
                                                pickup_date=pickup_date, 
                                                service_type=service_type, 
                                                service_title=service_title,
                                                service_count=service_count-1
                                                )
                    elif paid_orders.count() != orders_count:   
                        return HttpResponse('پرداخت کامل انجام نشده است') 
                    
                    #allocation
                    orders = Order.objects.filter(tracking_code=tracking_code)
                    district = None
                    pickup_date = None
                    last_order = orders.order_by('created_at').last()
                    pickup_date = last_order.pickup_date
                    pickup_time1 = last_order.service.pickup_time
                    sender_disp = last_order.dispatcher_sender
                    receiver_disp = last_order.dispatcher_reciever
                    zone = last_order.receiver_zone
                    service = last_order.service
                    business = last_order.user_business
                    
                    
                    dispatcher_order_counts = {}
                    dispatcher_sender_order_counts = {}

                    
                    ##allocation
                    dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
                    dispatcher_with_this_business = DispatcherProfile.objects.filter(business__id=business.id, confirm=True)
                    if not dispatchers_in_this_zone.exists():
                        dispatcher_receiver = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
                        if not dispatcher_with_this_business.exists():
                            dispatcher_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
                        else:
                            dispatcher_sender_order_counts = {}

                            # Count unique tracking codes for each dispatcher by pickup_date
                            for dispatcher in dispatcher_with_this_business:
                                order_sender_count = dispatcher.dispatcher_sender.filter(
                                    pickup_date=pickup_date,
                                    service=service
                                ).values('tracking_code').distinct().count()
                                dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                            min_sender_value = min(dispatcher_sender_order_counts.values())

                            # Find all keys that have the minimum value
                            min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                            # Randomly select one of the keys with the minimum value
                            selected_sender_key = random.choice(min_sender_keys)                                  
                            # if can_fit(big,medium,small):
                            dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()

                    else:                        

                        # Count unique tracking codes for each dispatcher by pickup_date
                        for dispatcher in dispatchers_in_this_zone:
                            order_count = dispatcher.dispatcher_reciever.filter(
                                pickup_date=pickup_date,
                                service=service
                            ).values('tracking_code').distinct().count()
                            dispatcher_order_counts[dispatcher.id] = order_count
                        min_value = min(dispatcher_order_counts.values())

                        # Find all keys that have the minimum value
                        min_keys = [key for key, value in dispatcher_order_counts.items() if value == min_value]

                        # Randomly select one of the keys with the minimum value
                        selected_key = random.choice(min_keys)                                  
                        # if can_fit(big,medium,small):
                        dispatcher_receiver = DispatcherProfile.objects.filter(id=selected_key).first()
                        if not dispatcher_with_this_business.exists() :
                            disp_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم')
                            if disp_sender:
                                dispatcher_sender = disp_sender.first()
                            else:
                                dispatcher_sender = dispatcher_receiver
                        else:
                            dispatcher_sender_order_counts = {}

                            # Count unique tracking codes for each dispatcher by pickup_date
                            for dispatcher in dispatcher_with_this_business:
                                order_sender_count = dispatcher.dispatcher_sender.filter(
                                    pickup_date=pickup_date,
                                    service=service
                                ).values('tracking_code').distinct().count()
                                dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                            min_sender_value = min(dispatcher_sender_order_counts.values())

                            # Find all keys that have the minimum value
                            min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                            # Randomly select one of the keys with the minimum value
                            selected_sender_key = random.choice(min_sender_keys)                                  
                            # if can_fit(big,medium,small):
                            dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()
                        ##end_of allocation
                    for order in orders:
                        order.dispatcher_sender = dispatcher_sender
                        order.dispatcher_reciever = dispatcher_receiver
                        order.save()
                    flag = False
                    
                if len(tracking_codes)==1:
                    tracking_code = next(iter(tracking_codes))
                    if user_phone is not None:
                        SendOrderSms(user_phone, tracking_code)
                    elif user_email is not None:
                        subject = 'ثبت سفارش در رایان'
                        message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {tracking_code}'

                        from_email = settings.EMAIL_HOST_USER  # Change this to your email
                        to_email = user_email

                        send_mail(subject, message, from_email, [to_email])
                else:
                    if user_phone is not None:
                        SendOrderMultiSms(user_phone, order_number)
                    elif user_email is not None:
                        subject = 'ثبت سفارش در رایان'
                        message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {order_number}'

                        from_email = settings.EMAIL_HOST_USER  # Change this to your email
                        to_email = user_email

                        send_mail(subject, message, from_email, [to_email])

                
                # Remove the tracking codes from the session after retrieving
                # if 'order_number' in request.session:
                #     del request.session['order_number']
                # #save tracking_codes in session
                # request.session['order_number'] = order_number

                # Redirect to a success page where tracking codes can be fetched
                return redirect(f'{site}/order/payment/success/?order_number={order_number}')

            elif t_status == 101:
                for tracking_code in tracking_codes:
                    orders = Order.objects.filter(tracking_code=tracking_code)
                    for order in orders:
                        order.bank_code = req.json()['data']['ref_id']
                        order.payment = 'Transaction submitted : ' + str(req.json()['data']['message'])
                        order.save()
                return redirect(f'{site}/order/payment/failed')
            else:
                for tracking_code in tracking_codes:
                    orders = Order.objects.filter(tracking_code=tracking_code)

                    for order in orders:
                        order.bank_code = req.json()['data']['ref_id']
                        order.payment = 'Transaction failed.\nStatus: ' + str(req.json()['data']['message'])
                        order.save()
                return redirect(f'{site}/order/payment/failed')

        else:
            e_code = req.json()['errors']['code']
            e_message = req.json()['errors']['message']
            for tracking_code in tracking_codes:
                orders = Order.objects.filter(tracking_code=tracking_code)

                for order in orders:
                    order.bank_code = req.json()['errors']['code']
                    order.payment = f"Error code: {e_code}, Error Message: {e_message}"
                    order.save()
            return redirect(f'{site}/order/payment/failed')

    else:
        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code)
            for order in orders:
                order.payment = 'Transaction failed or canceled by user'
                order.save()

        return redirect(f'{site}/order/payment/failed')

#saman
@csrf_exempt
def send_request_order_saman(request):
    global amount
    user_id = request.GET.get('id')
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return redirect(f'{site}/order/payment')
    bus_id = request.GET.get('bus_id')
    real = RealUserProfile.objects.filter(user=user).first()
    legal = LegalUserProfile.objects.filter(user_admin=user).first()
    user_phone = None
    user_email = None
    if user.phone is not None:
        user_phone = user.phone
    else:
        user_email = user.email


    if legal:
        orders = Order.objects.filter(user_business__legal_profile=legal,
                                      user_business__id=bus_id,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                      )
        if not orders.exists():
            return HttpResponse('Order not found', status=404)
    elif real:
        orders = Order.objects.filter(user_business__real_profile=real,
                                      user_business_id=bus_id,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                         )
        if not orders.exists():
            return HttpResponse('Order not found', status=404)

    else:
        return redirect(f'{site}/order/payment')
    current_time = datetime.datetime.now()
    current_date = current_time.date()
    current_jalali_date = str(jdatetime.date.fromgregorian(date=current_date))
    pickup_date= orders.first().pickup_date 
    service_time= orders.first().service.hour
    current_j_persian_date = english_to_persian_number(current_jalali_date.replace('-', '/'))
    if current_j_persian_date == pickup_date:
        if current_time.time() > service_time:
            return HttpResponse({'message':'زمان ثبت سفارش برای این سرویس در روز جاری به پایان رسیده است'}, status=status.HTTP_400_BAD_REQUEST)
        
    # if orders.first().service.title == 'سرویس درون شهری - عصرگاهی':
    #     if is_thursday(pickup_date):
    #         return HttpResponse({'message':'این سرویس در روزهای پنجشنبه فعال نیست'}, status=status.HTTP_404_NOT_FOUND)    
    tracking_codes = set()
    for order in orders:
        tracking_codes.add(order.tracking_code)

    #check the count of service and box
    amount = 0
    for tracking_code in tracking_codes:
        orders = Order.objects.filter(tracking_code=tracking_code).all()
        n1= n2= n3= 0
        last_order = orders.order_by('created_at').last()
        order_number = last_order.order_number
        for order in orders:
            if order.size.title == 'بزرگ':
                n1 += int(order.count)
            elif order.size.title == 'متوسط':
                n2 += int(order.count)
            elif order.size.title == 'کوچک':
                n3 += int(order.count)    
        # if can_fit(n1, n2, n3):
        pickup_date= last_order.pickup_date
        service_type= last_order.service.s_type
        service_title= last_order.service.title
        service_count= last_order.service.count
        check_service_count= CheckServiceCount.objects.filter(
            pickup_date=pickup_date, 
            service_type=service_type, 
            service_title=service_title).first()
        if check_service_count:
            if check_service_count.service_count<len(tracking_codes) or service_count<len(tracking_codes):
                return HttpResponse('متاسفانه سرویسی برای این تاریخ وجود ندارد', status=404)
        # else:
        #     return HttpResponse('تعداد بسته‌های انتخابی بیش از حد مجاز است', status=404) 
        #check disp for this zone
        disp = last_order.dispatcher_sender
        zone = last_order.receiver_zone
        service = last_order.service
                    
        if disp is not None:
            return HttpResponse('سفارش از قبل تخصیص داده شده', status=status.HTTP_400_BAD_REQUEST)
        
        dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
        
        # if not dispatchers_in_this_zone.exists():
        #     return HttpResponse(f'سفیری در این منطقه یافت نشد  {zone}.', status=status.HTTP_404_NOT_FOUND)
        
        amount += (last_order.total_price*10)

    random_num = random.randint(11111111,99999999)
    resnum = f'{random_num}{amount}'
    #change toman to rial
    amount = int(amount)
    req_data = {
    "action":"token",
    "TerminalId":Terminal_id_saman,
    "Amount":amount,
    "ResNum":resnum,
    "RedirectUrl":CallbackURLSaman,
    }
    if user_phone is not None:
        req_data["CellNumber"] = user_phone

    req_header = {"accept": "application/json", "content-type": "application/json'"}
    req = requests.post(url=saman_api_token, data=json.dumps(req_data), headers=req_header)
    if req.json()['status'] == 1:
        token = req.json()['token']
        PaymentAmount.objects.create(user=user, amount=amount, tracking_code=tracking_codes, authority=resnum)
        return redirect(f"https://sep.shaparak.ir/OnlinePG/SendToken?token={token}")
    else:
        e_code = req.json()['errorCode']
        e_message = req.json()['errorDesc']
        return HttpResponse(f"Error code: {e_code}, Error Message: {e_message}") 
    
def verify_transaction_order(terminal_number, ref_num):
    """
    ارسال درخواست POST به سرور VerifyTransaction برای تایید تراکنش.

    :param terminal_number: شماره ترمینال (TerminalNumber)
    :param ref_num: شماره مرجع تراکنش (RefNum)
    :return: پاسخ سرور به صورت JSON
    """
    url = "https://sep.shaparak.ir/VerifyTxnRandomSessionkey/ipg/VerifyTransaction"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "TerminalNumber": terminal_number,
        "RefNum": ref_num
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # بررسی خطاهای HTTP
        return response.json()  # پاسخ JSON
    except requests.exceptions.RequestException as e:
        return redirect(f'{site}/order/payment/failed')
        
@csrf_exempt
def verify_order_saman(request):
    authority = request.POST.get('ResNum')
    paied = PaymentAmount.objects.filter(authority=authority).first()
    if paied:
        tracking_code = ast.literal_eval(paied.tracking_code)
        tracking_codes = list(tracking_code)
        user = paied.user
        amount = paied.amount
        paied.date = datetime.datetime.now()
        paied.save()
    else:
        return redirect(f'{site}/order/payment/failed')
    real = RealUserProfile.objects.filter(user=user).first()
    legal = LegalUserProfile.objects.filter(user_admin=user).first()
    user_phone = None
    user_email = None
    if user.phone is not None:
        user_phone = user.phone
    else:
        user_email = user.email
    
    if legal:
        orders = Order.objects.filter(user_business__legal_profile=legal, 
                                      tracking_code__in=tracking_codes,
                                      payment_status=False,
                                      pursuit='waiting for payment'
                                      )
        order_number = orders.last().order_number
        if not orders.exists():
            return HttpResponse('خطایی مربوط به پروفایل یا کدرهگیری رخ داده', status=404)
    elif real:
        orders = Order.objects.filter(user_business__real_profile=real,
                                        tracking_code__in=tracking_codes,
                                        payment_status=False,
                                        pursuit='waiting for payment'
                                        )
        order_number = orders.last().order_number
        if not orders.exists():
            return HttpResponse('خطایی مربوط به پروفایل یا کدرهگیری رخ داده', status=406)
    else:
        return redirect(f'{site}/order/payment')
    t_status = request.POST.get('Status')
    refnum = request.POST.get('RefNum')
    if t_status == "2":
        logging.debug('t_status: 2')
        refnum = request.POST.get('RefNum')
        logging.debug(f'ref_num= {refnum}')

        try:
            # url_verify = "https://sep.shaparak.ir/VerifyTxnRandomSessionkey/ipg/VerifyTransaction"
            # req = requests.post(url=url_verify, headers=req_header, json=req_data)
            res = verify_transaction_order(Terminal_id_saman, f"{refnum}")
            if res["ResultCode"] == 0:
                logging.debug('resault_code = 0')
                logging.debug(f'data_for_check = {res}')
                if int(res["TransactionDetail"]["AffectiveAmount"])==int(amount):
                    logging.debug(f'amout is= {res["TransactionDetail"]["AffectiveAmount"]}')
                    paied.payment_status = True
                    paied.save()
                    
                    for tracking_code in tracking_codes:
                        orders = Order.objects.filter(tracking_code=tracking_code)
                        orders_count=len(orders)
                        flag = True
                        pickup_date = orders.first().pickup_date
                        for order in orders:
                            order.payment_status = True
                            order.bank_code = refnum
                            order.payment = 'Transaction success'
                            order.pursuit = 'waiting for collection'
                            if order.credit == True:
                                flag = False
                            order.credit = True
                            order.save()
                            # credit add
                            # value_id = order.value.id
                        paid_orders= Order.objects.filter(
                            tracking_code=tracking_code, 
                            payment_status = True
                            ) 
                        
                        #count service numbers for 
                        if paid_orders.count() == orders_count:
                            service_type = paid_orders.first().service.s_type
                            service_title = paid_orders.first().service.title  
                            service_count = paid_orders.first().service.count 
                            pickup_date= paid_orders.first().pickup_date
                            check_service_count= CheckServiceCount.objects.filter(
                            pickup_date=pickup_date, 
                            service_type=service_type, 
                            service_title=service_title).first() 
                            if check_service_count: 
                                check_service_count.service_count-=1 
                                check_service_count.save() 
                            elif not check_service_count:   
                                check_service_count= CheckServiceCount.objects.create(
                                                    pickup_date=pickup_date, 
                                                    service_type=service_type, 
                                                    service_title=service_title,
                                                    service_count=service_count-1
                                                    )
                        elif paid_orders.count() != orders_count:   
                            return HttpResponse('پرداخت کامل انجام نشده است') 
                        
                        #allocation
                        orders = Order.objects.filter(tracking_code=tracking_code)
                        district = None
                        pickup_date = None
                        last_order = orders.order_by('created_at').last()
                        pickup_date = last_order.pickup_date
                        pickup_time1 = last_order.service.pickup_time
                        disp = last_order.dispatcher_sender
                        zone = last_order.receiver_zone
                        service = last_order.service
                        business = last_order.user_business
                        
                        
                        # dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id)
                        
                        # if not dispatchers_in_this_zone.exists():
                        #     return HttpResponse(f'No dispatchers found for zone {zone}.', status=status.HTTP_404_NOT_FOUND)
                        
                        dispatcher_order_counts = {}
                        dispatcher_sender_order_counts = {}

                        
                        ##allocation
                        dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
                        dispatcher_with_this_business = DispatcherProfile.objects.filter(business__id=business.id, confirm=True)
                        if not dispatchers_in_this_zone.exists():
                            dispatcher_receiver = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
                            if not dispatcher_with_this_business.exists() :
                                dispatcher_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
                            else:
                                dispatcher_sender_order_counts = {}

                                # Count unique tracking codes for each dispatcher by pickup_date
                                for dispatcher in dispatcher_with_this_business:
                                    order_sender_count = dispatcher.dispatcher_sender.filter(
                                        pickup_date=pickup_date,
                                        service=service
                                    ).values('tracking_code').distinct().count()
                                    dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                                min_sender_value = min(dispatcher_sender_order_counts.values())

                                # Find all keys that have the minimum value
                                min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                                # Randomly select one of the keys with the minimum value
                                selected_sender_key = random.choice(min_sender_keys)                                  
                                # if can_fit(big,medium,small):
                                dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()

                        else:                        

                            # Count unique tracking codes for each dispatcher by pickup_date
                            for dispatcher in dispatchers_in_this_zone:
                                order_count = dispatcher.dispatcher_reciever.filter(
                                    pickup_date=pickup_date,
                                    service=service
                                ).values('tracking_code').distinct().count()
                                dispatcher_order_counts[dispatcher.id] = order_count
                            min_value = min(dispatcher_order_counts.values())

                            # Find all keys that have the minimum value
                            min_keys = [key for key, value in dispatcher_order_counts.items() if value == min_value]

                            # Randomly select one of the keys with the minimum value
                            selected_key = random.choice(min_keys)                                  
                            # if can_fit(big,medium,small):
                            dispatcher_receiver = DispatcherProfile.objects.filter(id=selected_key).first()
                            if not dispatcher_with_this_business.exists() :
                                disp_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم')
                                if disp_sender:
                                    dispatcher_sender = disp_sender.first()
                                else:
                                    dispatcher_sender = dispatcher_receiver
                            else:
                                dispatcher_sender_order_counts = {}

                                # Count unique tracking codes for each dispatcher by pickup_date
                                for dispatcher in dispatcher_with_this_business:
                                    order_sender_count = dispatcher.dispatcher_sender.filter(
                                        pickup_date=pickup_date,
                                        service=service
                                    ).values('tracking_code').distinct().count()
                                    dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                                min_sender_value = min(dispatcher_sender_order_counts.values())

                                # Find all keys that have the minimum value
                                min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                                # Randomly select one of the keys with the minimum value
                                selected_sender_key = random.choice(min_sender_keys)                                  
                                # if can_fit(big,medium,small):
                                dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()
                            ##end_of allocation
                        for order in orders:
                            order.dispatcher_sender = dispatcher_sender
                            order.dispatcher_reciever = dispatcher_receiver
                            order.save()
                    
                    
                    # end of allocation
                    if len(tracking_codes)==1:
                        tracking_code = next(iter(tracking_codes))
                        if user_phone is not None:
                            SendOrderSms(user_phone, tracking_code)
                        elif user_email is not None:
                            subject = 'ثبت سفارش در رایان'
                            message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {tracking_code}'

                            from_email = settings.EMAIL_HOST_USER  # Change this to your email
                            to_email = user_email

                            send_mail(subject, message, from_email, [to_email])
                    else:
                        if user_phone is not None:
                            SendOrderMultiSms(user_phone, order_number)
                        elif user_email is not None:
                            subject = 'ثبت سفارش در رایان'
                            message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {order_number}'

                            from_email = settings.EMAIL_HOST_USER  # Change this to your email
                            to_email = user_email

                            send_mail(subject, message, from_email, [to_email])

                    

                    # Redirect to a success page where tracking codes can be fetched
                    return redirect(f'{site}/order/payment/success/?order_number={order_number}')
                
                else:
                    return redirect(f'{site}/order/payment/failed')
            else:
                return redirect(f'{site}/order/payment/failed')

        except:
            e_message = "saman bank error"
            for tracking_code in tracking_codes:
                orders = Order.objects.filter(tracking_code=tracking_code)

                for order in orders:
                    order.bank_code = refnum
                    order.payment = f"Error Message: {e_message}"
                    order.save()
            return redirect(f'{site}/order/payment/failed')

    else:
        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code)
            for order in orders:
                order.payment = 'Transaction failed or canceled by user'
                order.save()

        return redirect(f'{site}/order/payment/failed')

@csrf_exempt
@api_view()
def send_request_order_wallet(request):
    user_id = request.GET.get('id')
    # user_id = request.user.id
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return Response({'message': 'کاربر یافت نشد'},status=status.HTTP_406_NOT_ACCEPTABLE)
    bus_id = request.GET.get('bus_id')
    real = RealUserProfile.objects.filter(user=user).first()
    legal = LegalUserProfile.objects.filter(user_admin=user).first()
    user_phone = None
    user_email = None
    if user.phone is not None:
        user_phone = user.phone
    else:
        user_email = user.email

    if legal:
        orders = Order.objects.filter(
            user_business__legal_profile=legal,
            user_business__id=bus_id,
            payment_status=False,
            pursuit='waiting for payment'
            )
    elif real:
        orders = Order.objects.filter(
            user_business__real_profile=real, 
            user_business__id=bus_id, 
            payment_status=False,
            pursuit='waiting for payment'
            )
    else:
        return Response({'message': 'پروفایل یافت نشد'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    
    if not orders:
        return Response({'message': 'سفارشی یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
    current_time = datetime.datetime.now()
    current_date = current_time.date()
    current_jalali_date = str(jdatetime.date.fromgregorian(date=current_date))
    pickup_date= orders.first().pickup_date 
    service_time= orders.first().service.hour
    current_j_persian_date = english_to_persian_number(current_jalali_date.replace('-', '/'))
    if current_j_persian_date == pickup_date:
        if current_time.time() > service_time:
            return Response({'message':'زمان ثبت سفارش برای این سرویس در روز جاری به پایان رسیده است'}, status=status.HTTP_400_BAD_REQUEST)
        
    # if orders.first().service.title == 'سرویس درون شهری - عصرگاهی':
    #     if is_thursday(pickup_date):
    #         return Response({'message':'این سرویس در روزهای پنجشنبه فعال نیست'}, status=status.HTTP_404_NOT_FOUND)    

    order_number = orders.last().order_number
    tracking_codes = set()
    for order in orders:
        tracking_codes.add(order.tracking_code)

    #check if price is more than wallet charge
    price_check = 0
    for tracking_code in tracking_codes:
        orders = Order.objects.filter(tracking_code=tracking_code)
        orders_count = len(tracking_codes)
        price_check += orders.order_by('created_at').last().total_price
        n1= n2= n3= 0
        last_order = orders.order_by('created_at').last()
        # for order in orders:
        #     if order.size.title == 'بزرگ':
        #         n1 += int(order.count)
        #     elif order.size.title == 'متوسط':
        #         n2 += int(order.count)
        #     elif order.size.title == 'کوچک':
        #         n3 += int(order.count)  
        # if can_fit(n1, n2, n3): 
        service_type = orders.first().service.s_type
        service_title = orders.first().service.title  
        pickup_date= orders.first().pickup_date  
        service_count= orders.first().service.count
        check_service_count= CheckServiceCount.objects.filter(
            pickup_date=pickup_date, 
            service_type=service_type, 
            service_title=service_title).first()
        if check_service_count:
            if check_service_count.service_count<orders_count or service_count<orders_count:
                return Response({'message': 'متاسفانه سرویسی برای این تاریخ وجود ندارد'}, status=status.HTTP_404_NOT_FOUND)
                
        # else:
        #     return Response({'message':'تعداد بسته ها بیش از حد مجاز است'}, status=status.HTTP_404_NOT_FOUND)
            
        #check dispatcher for this zone
        disp = last_order.dispatcher_sender
        zone = last_order.receiver_zone
        service = last_order.service
        
        dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
        
        # if not dispatchers_in_this_zone.exists():
        #     return Response({'message': f'سفیری در این منطقه وجود ندارد {zone}.'}, status=status.HTTP_404_NOT_FOUND)


    user_wallet = Wallet.objects.filter(user=user).first()
    if user_wallet:
        if price_check > user_wallet.amount:
            return Response({'message': 'موجودی کیف پول کافی نمی باشد'}, status=404)

    
    for tracking_code in tracking_codes:
        orders = Order.objects.filter(tracking_code=tracking_code)
        order_count= len(orders)      
        last_order = orders.order_by('created_at').last()

        service_type = orders.first().service.s_type
        service_title = orders.first().service.title  
        pickup_date= orders.first().pickup_date  
        service_count= orders.first().service.count
        check_service_count= CheckServiceCount.objects.filter(
            pickup_date=pickup_date, 
            service_type=service_type, 
            service_title=service_title).first()
        if check_service_count:
            if check_service_count.service_count==0 or service_count==0:
                return Response({'message': 'متاسفانه ظرفیت سرویس انتخابی برای این تاریخ به اتمام رسیده است'}, status=status.HTTP_404_NOT_FOUND)
        amount = last_order.total_price
        # amount = amount * 10
        user_wallet = Wallet.objects.filter(user=user).first()
        if user_wallet:
            if amount > user_wallet.amount:
                return Response({'message': 'موجودی کیف پول کافی نمی باشد'}, status=404)
        else:
            return Response({'message': 'کیف پول موجود نمی باشد'}, status=404)           
        
                       
            
        #allocation
        orders = Order.objects.filter(tracking_code=tracking_code)
        district = None
        pickup_date = None

        last_order = orders.order_by('created_at').last()
        pickup_date = last_order.pickup_date
        pickup_time1 = last_order.service.pickup_time
        disp = last_order.dispatcher_sender
        zone = last_order.receiver_zone
        service = last_order.service
        business = last_order.user_business
        
        # if disp is not None:
        #     return Response({'message': 'سفارش از قبل تخصیص داده شده'}, status=status.HTTP_400_BAD_REQUEST)

        # dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id)
        # if not dispatchers_in_this_zone.exists():
        #     return Response({'message': f'No dispatchers found for zone {zone}.'}, status=status.HTTP_404_NOT_FOUND)
        
        dispatcher_order_counts = {}
        dispatcher_sender_order_counts = {}

        # Count unique tracking codes for each dispatcher by pickup_date
        # for dispatcher in dispatchers_in_this_zone:
        #     order_count = dispatcher.dispatcher_sender.filter(
        #         pickup_date=pickup_date,
        #         service=service
        #     ).values('tracking_code').distinct().count()
        #     dispatcher_order_counts[dispatcher.id] = order_count
        # flag = True
        ##allocation
        dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
        dispatcher_with_this_business = DispatcherProfile.objects.filter(business__id=business.id, confirm=True)
        if not dispatchers_in_this_zone.exists():
            dispatcher_receiver = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
            if not dispatcher_with_this_business.exists() :
                dispatcher_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
            else:
                dispatcher_sender_order_counts = {}

                # Count unique tracking codes for each dispatcher by pickup_date
                for dispatcher in dispatcher_with_this_business:
                    order_sender_count = dispatcher.dispatcher_sender.filter(
                        pickup_date=pickup_date,
                        service=service
                    ).values('tracking_code').distinct().count()
                    dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                min_sender_value = min(dispatcher_sender_order_counts.values())

                # Find all keys that have the minimum value
                min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                # Randomly select one of the keys with the minimum value
                selected_sender_key = random.choice(min_sender_keys)                                  
                # if can_fit(big,medium,small):
                dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()

        else:                        

            # Count unique tracking codes for each dispatcher by pickup_date
            for dispatcher in dispatchers_in_this_zone:
                order_count = dispatcher.dispatcher_reciever.filter(
                    pickup_date=pickup_date,
                    service=service
                ).values('tracking_code').distinct().count()
                dispatcher_order_counts[dispatcher.id] = order_count
            min_value = min(dispatcher_order_counts.values())

            # Find all keys that have the minimum value
            min_keys = [key for key, value in dispatcher_order_counts.items() if value == min_value]

            # Randomly select one of the keys with the minimum value
            selected_key = random.choice(min_keys)                                  
            # if can_fit(big,medium,small):
            dispatcher_receiver = DispatcherProfile.objects.filter(id=selected_key).first()
            if not dispatcher_with_this_business.exists() :
                disp_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم')
                if disp_sender:
                    dispatcher_sender = disp_sender.first()
                else:
                    dispatcher_sender = dispatcher_receiver
            else:

                # Count unique tracking codes for each dispatcher by pickup_date
                for dispatcher in dispatcher_with_this_business:
                    order_sender_count = dispatcher.dispatcher_sender.filter(
                        pickup_date=pickup_date,
                        service=service
                    ).values('tracking_code').distinct().count()
                    dispatcher_sender_order_counts[dispatcher.id] = order_sender_count
                min_sender_value = min(dispatcher_sender_order_counts.values())

                # Find all keys that have the minimum value
                min_sender_keys = [key for key, value in dispatcher_sender_order_counts.items() if value == min_sender_value]

                # Randomly select one of the keys with the minimum value
                selected_sender_key = random.choice(min_sender_keys)                                  
                # if can_fit(big,medium,small):
                dispatcher_sender = DispatcherProfile.objects.filter(id=selected_sender_key).first()
            ##end_of allocation
        for order in orders:
            order.dispatcher_sender = dispatcher_sender
            order.dispatcher_reciever = dispatcher_receiver
            order.save()
    
        # end of allocation

        user_wallet.amount -= amount
        #increase wallet charge for every payment
        wallet_co = get_object_or_404(
            IncreaseWalletCo
        )
        coefficient = float(wallet_co.Coefficient)
        user_wallet.amount += amount*coefficient
        user_wallet.save()
        # this flag check if order has not been payed credit
        flag = True
        pickup_date = orders.first().pickup_date
        for order in orders:
            order.payment_status = True
            order.bank_code = 'wallet'
            order.payment = 'Transaction success'
            order.pursuit = 'waiting for collection'
            if order.credit == True:
                flag = False
            order.credit = True
            order.save()
            tracking_code_use = order.tracking_code
            # credit add
            # value_id = order.value.id
           
        if check_service_count: 
            check_service_count.service_count-=1 
            check_service_count.save() 
        elif not check_service_count:   
            check_service_count= CheckServiceCount.objects.create(
                                pickup_date=pickup_date, 
                                service_type=service_type, 
                                service_title=service_title,
                                service_count=service_count-1
                                )
            
    if len(tracking_codes)==1:
        tracking_code = next(iter(tracking_codes))
        if user_phone is not None:
            SendOrderSms(user_phone, tracking_code)
        elif user_email is not None:
            subject = 'ثبت سفارش در رایان'
            message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {tracking_code}'

            from_email = settings.EMAIL_HOST_USER  # Change this to your email
            to_email = user_email

            send_mail(subject, message, from_email, [to_email])
    else:
        if user_phone is not None:
            SendOrderMultiSms(user_phone, order_number)
        elif user_email is not None:
            subject = 'ثبت سفارش در رایان'
            message = f'سفارش شما با موفقیت در رایان ثبت شد. شماره سفارش: {order_number}'

            from_email = settings.EMAIL_HOST_USER  # Change this to your email
            to_email = user_email

            send_mail(subject, message, from_email, [to_email])

        # else:
        #     return Response({'message':'تعداد بسته‌های انتخابی بیش از حد مجاز است'}, status=404)

    
    return Response({f'message: با موفقیت ثبت شد. شماره سفارش {order_number}'})

@api_view(['GET'])
def get_tracking_codes(request):
    tracking_codes = request.session.get('tracking_codes', [])
    # Return the tracking codes as a response
    response = JsonResponse({'tracking_codes': tracking_codes})
    # Remove the tracking codes from the session after retrieving
    if 'tracking_codes' in request.session:
        del request.session['tracking_codes']
    return response

@csrf_exempt
def send_request_wallet(request): 
    user_id = request.GET.get('id')
    amount = request.GET.get('amount')
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return redirect(f'{site}/order/payment')
    #change toman to rial
    amount = int(amount)*10
    req_data = {
        "merchant_id": MERCHANT,
        "amount": amount,
        "callback_url": CallbackURL_wallet,
        "description": description,
        # "metadata": {"mobile": mobile, "email": email}
    }
    req_header = {"accept": "application/json", "content-type": "application/json'"}
    req = requests.post(url=ZP_API_REQUEST, data=json.dumps(req_data), headers=req_header)
    if len(req.json()['errors']) == 0:
        authority = req.json()['data']['authority']
        PaymentAmount.objects.create(user=user, amount=amount, tracking_code='wallet', authority=authority)
        return redirect(ZP_API_STARTPAY.format(authority=authority))
    else:
        e_code = req.json()['errors']['code']
        e_message = req.json()['errors']['message']
        print(f"Error code: {e_code}, Error Message: {e_message}")
        return redirect(f'{site}/dashboard/wallet/failed')



def verify_wallet(request):
    t_status = request.GET.get('Status')
    authority = request.GET['Authority']
    paied = PaymentAmount.objects.filter(authority=authority).first()
    if paied:
        amount = paied.amount
        user = paied.user
        paied.date = datetime.datetime.now()
        paied.save()
    else:
        return HttpResponse('خطایی اتفاق افتاده', status=406)

    if request.GET.get('Status') == 'OK':
        req_header = {"accept": "application/json", "content-type": "application/json'"}
        req_data = {
            "merchant_id": MERCHANT,
            "amount": amount,
            "authority": authority
        }
        req = requests.post(url=ZP_API_VERIFY, data=json.dumps(req_data), headers=req_header)

        if len(req.json()['errors']) == 0:
            t_status = req.json()['data']['code']

            if t_status == 100:
                paied.payment_status = True
                paied.save()
                wallet = get_object_or_404(
                    Wallet,
                    user=user,
                )
                had_amount = wallet.amount
                #change rial to toman
                w_amount = int(amount)/10
                #charge wallet 10% more than paied
                w_amount += w_amount/10
                w_amount += had_amount
                wallet.amount = w_amount
                wallet.save()

                return redirect(f'{site}/dashboard/wallet/success')

            elif t_status == 101:
                print('Transaction submitted : ' + str(req.json()['data']['message']))
                return redirect(f'{site}/dashboard/wallet/failed')

            else:
                print('Transaction failed.\nStatus: ' + str(req.json()['data']['message']))
                return redirect(f'{site}/dashboard/wallet/failed')

        else:
            e_code = req.json()['errors']['code']
            e_message = req.json()['errors']['message']
            print(f"Error code: {e_code}, Error Message: {e_message}")
            return redirect(f'{site}/dashboard/wallet/failed')

    else:
        print('Transaction failed or canceled by user')
        return redirect(f'{site}/dashboard/wallet/failed')


@csrf_exempt
def send_request_wallet_saman(request): 
    user_id = request.GET.get('id')
    amount = request.GET.get('amount')
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return redirect(f'{site}/order/payment')
    
    user_phone = None
    if user.phone:
        user_phone=user.phone
    random_num = random.randint(11111111,99999999)
    resnum = f'{random_num}{amount}'
    #change toman to rial
    amount = int(amount)*10
    req_data = {
    "action":"token",
    "TerminalId":Terminal_id_saman,
    "Amount":amount,
    "ResNum":resnum,
    "RedirectUrl":CallbackURL_walletSaman,
    }
    if user_phone is not None:
        req_data["CellNumber"] = user_phone

    req_header = {"accept": "application/json", "content-type": "application/json'"}
    req = requests.post(url=saman_api_token, data=json.dumps(req_data), headers=req_header)
    if req.json()['status'] == 1:
        token = req.json()['token']
        PaymentAmount.objects.create(user=user, amount=amount, tracking_code="wallet", authority=resnum)
        return redirect(f"https://sep.shaparak.ir/OnlinePG/SendToken?token={token}")
    else:
        e_code = req.json()['errorCode']
        e_message = req.json()['errorDesc']
        return HttpResponse(f"Error code: {e_code}, Error Message: {e_message}") 


def verify_transaction(terminal_number, ref_num):
    """
    ارسال درخواست POST به سرور VerifyTransaction برای تایید تراکنش.

    :param terminal_number: شماره ترمینال (TerminalNumber)
    :param ref_num: شماره مرجع تراکنش (RefNum)
    :return: پاسخ سرور به صورت JSON
    """
    url = "https://sep.shaparak.ir/VerifyTxnRandomSessionkey/ipg/VerifyTransaction"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "TerminalNumber": terminal_number,
        "RefNum": ref_num
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # بررسی خطاهای HTTP
        return response.json()  # پاسخ JSON
    except requests.exceptions.RequestException as e:
        logging.debug(f"sep_error: {e}")
        return redirect(f'{site}/dashboard/wallet/failed')


@csrf_exempt
def verify_wallet_saman(request):
    if request.method == "POST":
        authority = request.POST.get('ResNum')
        paied = PaymentAmount.objects.filter(authority=authority).first()
        if paied:
            amount = paied.amount
            user = paied.user
            paied.date = datetime.datetime.now()
            paied.save()
        else:
            return HttpResponse('خطایی اتفاق افتاده', status=406)


        t_status = request.POST.get('Status')
        if t_status == "2":
            refnum = request.POST.get('RefNum')
            try:
                # url_verify = "https://sep.shaparak.ir/VerifyTxnRandomSessionkey/ipg/VerifyTransaction"
                # req = requests.post(url=url_verify, headers=req_header, json=req_data)
                res = verify_transaction(Terminal_id_saman, f"{refnum}")
                if res["ResultCode"] == 0:
                    if int(res["TransactionDetail"]["AffectiveAmount"])==int(amount):
                
                        paied.payment_status = True
                        paied.save()
                        wallet = get_object_or_404(
                            Wallet,
                            user=user,
                        )
                        had_amount = wallet.amount
                        #change rial to toman
                        w_amount = int(amount)/10
                        #charge wallet 10% more than paied
                        w_amount += w_amount/10
                        w_amount += had_amount
                        wallet.amount = w_amount
                        wallet.save()

                        return redirect(f'{site}/dashboard/wallet/success')
                    else:
                        return redirect(f'{site}/dashboard/wallet/failed')
                        
                else:
                    return redirect(f'{site}/dashboard/wallet/failed')
            except requests.exceptions.RequestException as e:
                logging.debug(f"sep_error: {e}")
                return redirect(f'{site}/dashboard/wallet/failed')

                

        else:
            return redirect(f'{site}/dashboard/wallet/failed')

    

    else:
        # e_code = req.json()['errors']['code']
        # e_message = req.json()['errors']['message']
        return redirect(f'{site}/dashboard/wallet/failed')


