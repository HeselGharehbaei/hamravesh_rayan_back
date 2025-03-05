import datetime
import jdatetime
import random
import string
import requests
import re
from persiantools.jdatetime import JalaliDate
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.db import transaction
from config.settings import API_KEY
from cities.models import City, State
from dispatcher_profile.models import DispatcherProfile
from payment.models import Wallet
from options.models import CheckServiceCount, Service, Size, Content
from core.utils.constant import tax_co
from payment.models import IncreaseWalletCo
from .models import Order
from django.db import transaction
from core.utils.validations import validate_date_within_10_days_and_jalali_date_format


rayan_data={
  "status": "OK",
  "neighbourhood": "شیخ هادی",
  "municipality_zone": "11",
  "state": "استان تهران",
  "city": "تهران",
  "route_name": "نوفل لوشاتو",
  "route_type": "secondary",
  "district": "بخش مرکزی شهرستان تهران",
  "formatted_address": "تهران، ولیعصر، نوفل لوشاتو، بین هانری کوربن و یاسمن، شرکت رایان پست",
  "lat": 35.696962806429504,
  "lng": 51.408145413815134,
}


rayan_data = {
    "status": "OK",
    "neighbourhood": "شیخ هادی",
    "municipality_zone": "11",
    "state": "استان تهران",
    "city": "تهران",
    "route_name": "نوفل لوشاتو",
    "route_type": "secondary",
    "district": "بخش مرکزی شهرستان تهران",
    "formatted_address": "تهران، ولیعصر، نوفل لوشاتو، بین هانری کوربن و یاسمن، شرکت رایان پست",
    "lat": 35.696962806429504,
    "lng": 51.408145413815134,
}

receiver_data = {
    "status": None,
    "neighbourhood": "خیابان جمهوری",
    "municipality_zone": None,
    "state": None,
    "city": None,
    "route_name": None,
    "route_type": "primary",
    "district": None,
    "formatted_address": None,
    "lat": None,
    "lng": None,
}

sender_data = {
    "status": "PENDING",
    "neighbourhood": None,
    "municipality_zone": "12",
    "state": "استان تهران",
    "city": None,
    "route_name": None,
    "route_type": None,
    "district": "بخش شرقی",
    "formatted_address": None,
    "lat": None,
    "lng": None,
}

def fill_specific_keys(target_data, reference_data, keys):
    """
    بررسی و جایگزینی مقادیر None فقط برای کلیدهای مشخص شده.
    """
    for key in keys:
        if key in target_data and (target_data[key] is None or target_data[key] == ""):
            target_data[key] = reference_data.get(key)

# کلیدهای مورد نظر برای بررسی
keys_to_check = ["neighbourhood", "municipality_zone"]


phone_pattern_iran = r'^09\d{9}$'

def validate_phone_number(phone_number):
    if not re.match(phone_pattern_iran, phone_number):
        raise serializers.ValidationError({'message':'شماره تلفن معتبر نیست.'})
    return phone_number


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
        raise ValueError('لت و لانگ مورد قبول نیست (در صورتی که فیلترشکن شما روشن است آن را خاموش کنید.) ') 
 

def get_location(address):
    """
    Function to get the geolocation details from the Neshan API based on latitude and longitude.
    """
    try:
        # Define the Neshan API URL and headers
        url = f'https://api.neshan.org/v6/geocoding?address={address}'
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

        raise ValueError('آدرس مورد قبول نیست (در صورتی که فیلترشکن شما روشن است آن را خاموش کنید.) ') 
    

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


def generate_traking_code():
    letters_first = ''.join(random.choices(string.ascii_uppercase, k=2))
    letters_last = ''.join(random.choices(string.ascii_uppercase, k=2))

    # Generate random numbers for the middle part
    numbers = ''.join(random.choices(string.digits, k=9))

    # Concatenate the parts to form the code
    tracking_code = letters_first + numbers + letters_last
    return tracking_code

def generate_delivery_code():
    delivery_code = random.randint(1000, 9999)
    return delivery_code

def generate_order_number():
    order_number = random.randint(1000, 9999)
    return order_number


def SendApiOrderSms(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        # 'token2': token2,
        'template': 'OrderApi'
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

def persian_to_english_number(persian_str):
    # Define a mapping from English digits to Persian digits
    persian_to_english_map = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    # Replace each English digit with the corresponding Persian digit
    english_str = ''.join(persian_to_english_map.get(char, char) for char in persian_str)
    return english_str

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
    

class OrderSerializer(serializers.Serializer):

    small_size_count = serializers.CharField(default= '0', allow_blank=False,)
    medium_size_count = serializers.CharField(default= '0', allow_blank=False,)
    big_size_count = serializers.CharField(default= '0', allow_blank=False,)
    sender_title = serializers.CharField(required=True, allow_blank=False, max_length=50)
    sender_plaque = serializers.CharField(required=True, allow_blank=False, max_length=20,)
    sender_unity = serializers.CharField(required=True, allow_blank=False, max_length=10,)
    sender_name = serializers.CharField(required=True, allow_blank=False, max_length=100,)
    sender_phone = serializers.CharField(required=True, allow_blank=False, validators=[validate_phone_number], max_length=11)  
    sender_state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), required=True)
    sender_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), required=True)
    sender_address= serializers.CharField(required=False, max_length=200)
    sender_lat= serializers.CharField(required=False, max_length=20)
    sender_long= serializers.CharField(required=False, max_length=20)
    receiver_lat= serializers.CharField(required=False, max_length=20)
    receiver_long= serializers.CharField(required=False, max_length=20)
    receiver_title = serializers.CharField(required=True, allow_blank=False, max_length=50)
    receiver_plaque = serializers.CharField(required=True, allow_blank=False, max_length=20,)
    receiver_unity = serializers.CharField(required=True, allow_blank=False, max_length=10,)
    receiver_name = serializers.CharField(required=True, allow_blank=False, max_length=100,)
    receiver_phone = serializers.CharField(required=True, allow_blank=False, validators=[validate_phone_number], max_length=11)
    receiver_address= serializers.CharField(required=False, max_length=200)
    receiver_state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), required=True)
    receiver_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), required=True)    
    service= serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=True)
    content= serializers.PrimaryKeyRelatedField(queryset=Content.objects.all(), required=True)
    value= serializers.CharField(required=True, allow_blank=False)
    pickup_date= serializers.CharField(required=True, allow_blank=False, validators=[validate_date_within_10_days_and_jalali_date_format])
    address_description= serializers.CharField(default='', )

        
    def validate(self, validated_data):
        business = self.context['business']
        user= self.context['user']
        pickup_date= validated_data['pickup_date']
        sender_lat = validated_data.get('sender_lat')
        sender_long = validated_data.get('sender_long')
        sender_address = validated_data.get('sender_address')
        receiver_lat = validated_data.get('receiver_lat')
        receiver_long = validated_data.get('receiver_long')
        receiver_address = validated_data.get('receiver_address')
        sender_phone_number= persian_to_english_number(validated_data['sender_phone'])
        receiver_phone_number= persian_to_english_number(validated_data['receiver_phone'])
        #check sender_lat and long or sender_address is existed 
        if (not sender_lat or not sender_long) and not sender_address:
            raise serializers.ValidationError({'message':'آدرس یا(لت و لانگ) فرستنده باید پر باشد'}) 

        #check receiver_lat and long or receiver_address is existed 
        if (not receiver_lat or not receiver_long) and not receiver_address:
            raise serializers.ValidationError({'message':'آدرس یا(لت و لانگ) گیرنده باید پر باشد'}) 
        
        numeric_fields = [validated_data.get('small_size_count'), validated_data.get('medium_size_count'), validated_data.get('big_size_count')]
        for field in numeric_fields:
            if not field.isdigit():
                raise serializers.ValidationError({field: f"مقدار '{field}' باید یک مقدار عددی باشد."})
        small_size_count = int(validated_data['small_size_count'])
        medium_size_count = int(validated_data['medium_size_count'])
        big_size_count= int(validated_data['big_size_count'])      
        service = validated_data['service']
        if not Service.objects.filter(id= service.id).filter:
            raise serializers.ValidationError({'message':"سرویس یافت نشد"}) 
        service_title =  service.title
        service_type = service.s_type
        service_count = service.count
        service_price = service.price
        pickup_date = english_to_persian_number(pickup_date)
        check_service_count= CheckServiceCount.objects.filter(
            pickup_date=pickup_date,
            service_type=service_type, 
            service_title=service_title).first()
        if check_service_count:
            if check_service_count.service_count==0 or service_count==0:
                raise serializers.ValidationError({'message':"متاسفانه سرویسی برای این تاریخ وجود ندارد"})  
                #check all counts for orders
        pursuit = 'waiting for collection'
        count_box = 0
        val = validated_data['value']
        val = int(val)
        if val<1000000 and val>0:
            val_price = 2000
        elif val>=1000000 and val<=20000000:
            val_price = float(val*0.002)
        elif val>20000000 and val<=50000000:
            val_price=float(val*0.003)
        else:
            raise serializers.ValidationError({'message':'ارزش نامعتبر است'}) 
        #check size count is existed 
        size_list = [{'کوچک':small_size_count}, {'متوسط':medium_size_count}, {'بزرگ':big_size_count}] 
        if small_size_count==0 and medium_size_count==0 and big_size_count==0:
            raise serializers.ValidationError({'message':'حداقل یکی ازفیلدهای تعداد بسته ها باید غیر صفر باشد'})
        if small_size_count == 0:
            size_list.remove({'کوچک':small_size_count})
        if medium_size_count == 0:
            size_list.remove({'متوسط':medium_size_count})
        if big_size_count == 0:
            size_list.remove({'بزرگ':big_size_count})        
        total_box_count= small_size_count+medium_size_count+big_size_count
        decrease_count= 0
        if total_box_count >=2:
            decrease_count= total_box_count -1
        on_small_size_price= float(service_price) * (1 + float(Size.objects.filter(title='کوچک').first().price_co))     
        small_size_price = float(service_price) * (1 + float(Size.objects.filter(title='کوچک').first().price_co)) * small_size_count            
        medium_size_price = float(service_price) * (1 + float(Size.objects.filter(title='متوسط').first().price_co)) * medium_size_count
        big_size_price = float(service_price) * (1 + float(Size.objects.filter(title='بزرگ').first().price_co)) * big_size_count
        main_total_price = (small_size_price + medium_size_price + big_size_price) - (on_small_size_price * decrease_count * 0.3)
        total_price= (main_total_price+ val_price)*(1+tax_co)
        wallet = Wallet.objects.get(user=user) 
        if wallet.amount < total_price:
            raise serializers.ValidationError({"message": "هزینه سفارش بیشتر از موجودی کیف پول است"}) 
        today_gregorian = datetime.datetime.now().date()
        today_datetime = str(jdatetime.date.fromgregorian(date=today_gregorian)).replace('-', '/')
        today_datetime = english_to_persian_number(today_datetime)
        pickup_date_ex = pickup_date
        if pickup_date_ex.replace(" ", "") == today_datetime:
            request_time = datetime.datetime.now()
            if request_time.time() >= service.hour:
                if (business.id=='C3YS' and service.id == '10L9' and request_time.time() <= datetime.time(9, 15, 0)):
                    pass
                elif (business.id=='C3YS' and service.id == 'C7HI' and request_time.time() <= datetime.time(14, 30, 0)):
                    pass
                else:
                    raise serializers.ValidationError({'message':'زمان انتخاب این سرویس گذشته است'})
        if  sender_lat and sender_long :
            try:
                sender_data = get_geolocation(sender_lat, sender_long)
                sender_address = sender_data['formatted_address']
            except:
                sender_lat= rayan_data['lat']
                sender_long= rayan_data['lng']
                sender_address = rayan_data['formatted_address']
                sender_data= rayan_data
        else:
            try:
                sender_lat = get_location(f'تهران، {sender_address}')['location']['y']
                sender_long = get_location(f'تهران، {sender_address}')['location']['x']
                sender_data = get_geolocation(sender_lat, sender_long) 
            except:
                sender_data= rayan_data
                sender_address= rayan_data['formatted_address']
                sender_lat= rayan_data['lat']
                sender_long= rayan_data['lng']

        if receiver_lat and receiver_long  :
            try:
                receiver_data = get_geolocation(receiver_lat, receiver_long)
                receiver_address = receiver_data['formatted_address']
            except:
                receiver_address = rayan_data['formatted_address']
                receiver_data= rayan_data
                receiver_lat= rayan_data['lat']
                receiver_long= rayan_data['lng']

        else:
            try:
                receiver_lat = get_location(f'تهران، {receiver_address}')['location']['y']
                receiver_long = get_location(f'تهران، {receiver_address}')['location']['x'] 
                receiver_data = get_geolocation(receiver_lat, receiver_long)
            except:
                receiver_address = rayan_data['formatted_address']
                receiver_data= rayan_data
                receiver_lat= rayan_data['lat']
                receiver_long= rayan_data['lng']
        # پر کردن مقادیر None فقط برای کلیدهای مشخص شده
        fill_specific_keys(receiver_data, rayan_data, keys_to_check)
        fill_specific_keys(sender_data, rayan_data, keys_to_check) 
        # Access the related CustomUser through the business (assuming there's a OneToOne or ForeignKey relationship)
        business_user = business.legal_profile.user_admin if business.legal_profile else business.real_profile.user
        if user != business_user:
            raise serializers.ValidationError({'message':'کاربر اجازه ثبت سفارش با این کسب و کار را ندار'}) 

        sender_state= validated_data['sender_state']
        sender_city= validated_data['sender_city']  
        if not State.objects.filter(id=sender_state.id) or not City.objects.filter(id=sender_city.id):
            raise serializers.ValidationError({'message':'آدرس یا لت و لانگ وارد شده برای فرستنده خارج از تهران است'})
        receiver_state= validated_data['receiver_state']
        receiver_city= validated_data['receiver_city']
        if not State.objects.filter(id=receiver_state.id) or not City.objects.filter(id=receiver_city.id ):
            raise serializers.ValidationError({'message':'آدرس یا لت و لانگ وارد شده برای گیرنده خارج از تهران است'})            
        # Retrieve the Wallet associated with the CustomUser               
        content = validated_data['content']
        # If any critical fields are missing, log the error and skip the row
        if not Content.objects.filter(id=content.id):
            raise serializers.ValidationError({'message':'محتوا یافت نشد'})      
        orders_list = []  # لیست برای ذخیره اوردرها
        tracking_code= generate_traking_code()
        order_number= generate_order_number()
        delivery_code= generate_delivery_code()
        wallet_co = get_object_or_404(
            IncreaseWalletCo
        )
        ##allocation
        zone = receiver_data['municipality_zone']
        dispatcher_order_counts = {}
        dispatcher_sender_order_counts = {}
        dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id, confirm=True)
        dispatcher_with_this_business = DispatcherProfile.objects.filter(business__id=business.id, confirm=True)
        if not dispatchers_in_this_zone.exists():
            # raise serializers.ValidationError({'message':f'متاسفانه سفیری برای منطقه{zone} وجود ندارد'}) 
            dispatcher_receiver = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
            if not dispatcher_with_this_business.exists():
                dispatcher_sender = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first()
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
        try:
            with transaction.atomic():
                for size_d in size_list:                    
                    size_title = next(iter(size_d))
                    size = Size.objects.filter(title=size_title).first()         
                    count_box = size_d[size_title]
                    decrease_count= 0
                    if count_box == 0:
                        continue
                    # Generate unique tracking code
                    size_price = float(size.price_co) * service_price
                    # count_box_new = int(row['تعداد'])
                    if count_box >= 2:
                        decrease_count = count_box
                    price = ((int(service_price) + float(size_price)) * int(count_box))-((float(service_price)*(1+(float(get_object_or_404(Size, title='کوچک').price_co))))*decrease_count*0.3)                  
                        

                        
                    order = Order.objects.create(
                        user_business=business,
                        address_description=validated_data['address_description'],
                        size=size,
                        count=count_box,
                        content=content,
                        service=service,
                        value=val,
                        pickup_date=pickup_date,
                        order_number=order_number,
                        receiver_title=validated_data['receiver_title'],
                        sender_title=validated_data['sender_title'],
                        sender_state=sender_state,
                        sender_city=sender_city,
                        sender_address=sender_address,
                        sender_zone=sender_data['municipality_zone'],
                        sender_district=sender_data['neighbourhood'],
                        sender_plaque=validated_data['sender_plaque'],
                        sender_unity=validated_data['sender_unity'],
                        sender_name=validated_data['sender_name'],
                        sender_phone=sender_phone_number,
                        sender_lat=sender_lat,
                        sender_long=sender_long,
                        sender_map_link=f'https://nshn.ir/?lat={sender_lat}&lng={sender_long}',
                        dispatcher_sender=dispatcher_sender,
                        receiver_state=receiver_state,
                        receiver_city=receiver_city,
                        receiver_address=receiver_address,
                        receiver_zone=receiver_data['municipality_zone'],
                        receiver_district=receiver_data['neighbourhood'],
                        receiver_plaque=validated_data['receiver_plaque'],
                        receiver_unity=validated_data['receiver_unity'],
                        receiver_name=validated_data['receiver_name'],
                        receiver_phone= receiver_phone_number,
                        receiver_lat=receiver_lat,
                        receiver_long=receiver_long,
                        receiver_map_link=f'https://nshn.ir/?lat={receiver_lat}&lng={receiver_long}',
                        dispatcher_reciever=dispatcher_receiver,
                        price=price,
                        total_price=total_price,
                        tracking_code=tracking_code,
                        delivery_code=delivery_code,
                        pursuit=pursuit,
                        payment_status=True,
                        credit=True,
                        payment='api',
                        bank_code='api',
                        is_multi= False,
                    )        
                    orders_list.append(order)
                if len(orders_list)==len(size_list):
                    coefficient = float(wallet_co.Coefficient)
                    wallet.amount -= total_price
                    wallet.amount += total_price*coefficient
                    wallet.save() 
                    if check_service_count:
                        check_service_count.service_count-=1
                        check_service_count.save() 
                    else:
                        check_service_count= CheckServiceCount.objects.create(
                            pickup_date= pickup_date,
                            service_count= service.count -1,
                            service_title= service.title,
                            service_type= service.s_type)
                    return {
                    "orders_list": orders_list,
                    "total_box_count": total_box_count,
                    "tracking_code": tracking_code
                    }  
                      
        except Exception as e:              
            raise serializers.ValidationError({'message':f"Error occurred: {e}"})  

