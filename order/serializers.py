import datetime
import jdatetime
import random
import re
import string
from jsonschema import ValidationError
import pandas as pd
import requests

from persiantools.jdatetime import JalaliDate
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from jalali_date import datetime2jalali
from rest_framework import serializers
from django.db import transaction
from django.apps import apps

from config import settings
from config.settings import API_KEY
from business.models import Business
from cities.models import City, State
from cities.serializers import DistrictSerializer, CitySerializer, StateSerializer
from dispatcher_payment.views import transform_time_range
from dispatcher_profile.models import DispatcherProfile
from payment.api_views import SendFreeDispatcher
from payment.models import Wallet
from userprofile.models import RealUserProfile, LegalUserProfile
from options.models import CheckServiceCount, Service, Size, Value, Content, Package
from options.serializers import ServiceSerializers, SizeSerializers, ValueSerializers, ContentSerializers, PackageSerializers
from core.utils.constant import tax_co
from prices.views import can_fit
from payment.models import IncreaseWalletCo
from .models import Order, ProcessExcel


city_id = City.objects.filter(name="تهران").first()
state_id = State.objects.filter(name="تهران").first()
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
  "city_id": city_id,
  "state_id": state_id
}


def SendExcelOrderSms(receptor, token):
    url = f'https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json'
    data = {
        'receptor': receptor,
        'token': token,
        # 'token2': token2,
        'template': 'OrderExcel'
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
    

class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        # fields = '__all__'
        exclude = ['user_business']

    def get_restricted_fields(self):
        """
        Returns a list of field names in the `Order` model that do not include
        the substrings 'receiver' or 'sender'.
        """
        try:
            # Dynamically fetch the Order model
            order_model = apps.get_model('order', 'Order')
        except LookupError:
            raise serializers.ValidationError('Order model could not be found.')

        # Retrieve all field names
        all_fields = [field.name for field in order_model._meta.fields]

        # Exclude fields containing "receiver" or "sender"
        restricted_fields = [
            field for field in all_fields
            if "receiver" not in field.lower() and "sender" not in field.lower()
        ]

        return restricted_fields

    def get_business(self):
        user = self.context['request'].user
        bus_id = self.context['view'].kwargs.get('id')
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()

        if legal:
            return get_object_or_404(Business, id=bus_id, legal_profile=legal)
        elif real:
            return get_object_or_404(Business, id=bus_id, real_profile=real)
        else:
            raise serializers.ValidationError('ابتدا پروفایل خود را تکمیل کنید')                    

        
    def create(self, validated_data):
        business = self.get_business()
        pursuit = 'waiting for payment'
        count_box = 0
        this_order_count = 0
        order_number_check = False
        total_count = int(validated_data['count'])
        #check all counts for orders
        check_total_count_orders = Order.objects.filter(user_business=business,
                                       payment_status=False,
                                       pickup_date=validated_data['pickup_date'],
                                       service=validated_data['service'],
                                       pursuit='waiting for payment', pre_order=0)
        
        if check_total_count_orders:
            tracking_codes = set()
            order_number = check_total_count_orders.last().order_number
            order_number_check = True
            for order in check_total_count_orders:
                total_count += order.count
                tracking_codes.add(order.tracking_code)

            for tracking_code in tracking_codes:
                orders = Order.objects.filter(tracking_code=tracking_code)
                total_just_price = sum(order.price for order in orders)
                order_count = 0
                order_count += sum(order.count for order in orders)
                
                for order in orders: 
                    if (
                    order.receiver_lat == validated_data['receiver_lat'] 
                    and order.receiver_long == validated_data['receiver_long'] 
                    and order.receiver_phone == validated_data['receiver_phone']
                    ):
                        if len(tracking_codes)==1:
                            this_order_count = sum(order.count for order in orders)
                            break
                        else:
                            order_count += validated_data['count']
                    val = order.value
                    val = int(val)
                    if val<1000000 and val>0:
                        val_price = 2000
                    elif val>=1000000 and val<=20000000:
                        val_price = float(val*0.002)
                    elif val>20000000 and val<=50000000:
                        val_price=float(val*0.003)
                    else:
                        raise ValidationError('ارزش نامعتبر است')
                    total_insurance = val_price
                    divided_insurance = total_insurance * float(order_count/total_count)
                    change_price_for_divide_insurance = tax_co*float(total_insurance-divided_insurance)
                    order.total_price = total_just_price + change_price_for_divide_insurance + divided_insurance
                    order.save()

        # Check if there is an existing order for the user
        orders = Order.objects.filter(user_business=business,
                                       payment_status=False,
                                       sender_lat=validated_data['sender_lat'], sender_long=validated_data['sender_long'],
                                       receiver_lat=validated_data['receiver_lat'], receiver_long=validated_data['receiver_long'],
                                       receiver_phone=validated_data['receiver_phone'],
                                       pickup_date=validated_data['pickup_date'],
                                       service=validated_data['service'],
                                       pursuit='waiting for payment', pre_order=0)
        if orders:
            tracking_code = orders.first().tracking_code
            delivery_code = orders.first().delivery_code
            order_number = orders.first().order_number
            flag_for_count = True
            for order in orders:
                count_box += order.count

                                    
        else:
            flag_for_count = False
            # Generate a unique tracking code and  order_number
            while True:
                
                letters_first = ''.join(random.choices(string.ascii_uppercase, k=2))
                letters_last = ''.join(random.choices(string.ascii_uppercase, k=2))

                # Generate random numbers for the middle part
                numbers = ''.join(random.choices(string.digits, k=9))

                # Concatenate the parts to form the code
                tracking_code = letters_first + numbers + letters_last

                if not Order.objects.filter(tracking_code=tracking_code).exists():
                    delivery_code = random.randint(1000, 9999)
                    if not order_number_check:
                        order_number = random.randint(1000, 9999)
                    break
        
        service_price = get_object_or_404(Service, id=validated_data['service'].id).price
        size_price = float(get_object_or_404(Size, id=validated_data['size'].id).price_co) * int(service_price)
        #count how many box doese exist
        if count_box == 0:
            count_box = int(validated_data['count'])
        else:
            count_box += int(validated_data['count'])
        
        if count_box >= 2:
            if flag_for_count:
                decrease_count = int(validated_data['count'])
            else:
                decrease_count = int(validated_data['count'])-1

            price = ((int(service_price) + float(size_price)) * int(validated_data['count']))-((float(service_price)+(float(get_object_or_404(Size, title='کوچک').price_co) * int(service_price)))*decrease_count*0.3)
            
        else:
            price = (int(service_price) + int(size_price)) * int(validated_data['count'])
        total_orders = Order.objects.filter(user_business=business,
                                       payment_status=False,
                                       sender_lat=validated_data['sender_lat'], sender_long=validated_data['sender_long'],
                                       receiver_lat=validated_data['receiver_lat'], receiver_long=validated_data['receiver_long'],
                                       receiver_phone=validated_data['receiver_phone'],
                                       pickup_date=validated_data['pickup_date'],
                                       service=validated_data['service'],
                                       pursuit='waiting for payment',).all()
        
        total_order = total_orders.order_by('created_at').last()
        
        val = validated_data['value']

               

        if total_order:
            total_price = total_order.total_price
            total_price += price
            #tax
            total_price += tax_co*price
            for order in total_orders:
                order.total_price = total_price
                order.save()
        else:
            #insurance
            val = int(val)
            if val<1000000 and val>0:
                val_price = 2000
            elif val>=1000000 and val<=20000000:
                val_price = float(val*0.002)
            elif val>20000000 and val<=50000000:
                val_price=float(val*0.003)
            else:
                raise ValidationError('ارزش معتبر نمیباشد')
            
            total_price = price + (val_price)*float(int((validated_data['count'])+this_order_count)/total_count)
            #tax
            total_price += tax_co*total_price

        service_id = validated_data['service'].id
        service = Service.objects.filter(id=service_id).first()
        current_time = datetime.datetime.now()
        current_date = current_time.date()
        current_jalali_date = str(jdatetime.date.fromgregorian(date=current_date))
        current_j_persian_date = english_to_persian_number(current_jalali_date.replace('-', '/'))
        pickup_date = validated_data['pickup_date']
        if current_j_persian_date == pickup_date:
            if current_time.time() > service.hour:
                if (business.id=='C3YS' and service.id == '10L9' and current_time.time() <= datetime.time(9, 15, 0)):
                    pass
                elif (business.id== 'C3YS' and service.id == 'C7HI' and current_time.time() <= datetime.time(14, 30, 0)):
                    pass
                else:
                    raise serializers.ValidationError({'message':'زمان ثبت سفارش برای این سرویس در روز جاری به پایان رسیده است'})
            
        # if service.title == 'سرویس درون شهری - عصرگاهی':
        #     if is_thursday(pickup_date):
        #         raise serializers.ValidationError({'message':'این سرویس در روزهای پنجشنبه فعال نیست'})

        # Create the order
        order = Order.objects.create(
            user_business=business,
            order_number=order_number,
            pursuit=pursuit,
            price=price,
            total_price=total_price,
            tracking_code=tracking_code,
            delivery_code=delivery_code,
            **validated_data
        )
        order.created_at = datetime2jalali(order.created_at)
        order.updated_at = datetime2jalali(order.updated_at)
        return order


    # def update(self, instance, validated_data):
    #     restricted_fields = self.get_restricted_fields()

    #     # Remove restricted fields from validated_data
    #     for field in restricted_fields:
    #         validated_data.pop(field, None)

    #     tracking_code = self.context['view'].kwargs.get('tracking_code')
    #     orders = Order.objects.filter(tracking_code=tracking_code)
    #     bus_id = orders.first().user_business.id
    #     user = self.context['request'].user
    #     legal = LegalUserProfile.objects.filter(user_admin=user).first()
    #     real = RealUserProfile.objects.filter(user=user).first()

    #     if legal:
    #         business = get_object_or_404(Business, id=bus_id, legal_profile=legal)
    #     elif real:
    #         business = get_object_or_404(Business, id=bus_id, real_profile=real)
    #     else:
    #         raise serializers.ValidationError('ابتدا پروفایل خود را تکمیل کنید')

    #     if (instance.user_business.legal_profile == business.legal_profile) or (instance.user_business.real_profile == business.real_profile):
    #         updated_orders = []
    #         for order in orders:
    #             for key, value in validated_data.items():
    #                 setattr(order, key, value)
    #             order.save()
    #             updated_orders.append(order)

    #         # Optionally, return the first updated order or a custom response
    #         return updated_orders  # Return the list of updated order instances
    #     else:
    #         raise serializers.ValidationError('کاربر اجازه تغییر ندارد')


class OrderListSerializer(serializers.ModelSerializer):
    service = ServiceSerializers()
    size = SizeSerializers()
    content = ContentSerializers()
    package = PackageSerializers()
    sender_city = CitySerializer()
    receiver_city = CitySerializer()
    sender_state = StateSerializer()
    receiver_state = StateSerializer()


    class Meta:
        model = Order
        fields = '__all__'

    def to_representation(self, instance):
        # Customize the representation of the serialized data here
        representation = super().to_representation(instance)
        # Add or modify fields in the 'representation' dictionary as needed
        original_datetime_str_c = representation['created_at']
        original_datetime_str_u = representation['updated_at']
        original_datetime_c = datetime.datetime.strptime(original_datetime_str_c, "%Y/%m/%d %H:%M:%S")
        original_datetime_u = datetime.datetime.strptime(original_datetime_str_u, "%Y/%m/%d %H:%M:%S")
        formatted_datetime_c = datetime2jalali(original_datetime_c)
        formatted_datetime_u = datetime2jalali(original_datetime_u)
        changed_format_datetime_c = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
        changed_format_datetime_u = formatted_datetime_u.strftime("%Y/%m/%d %H:%M:%S")
        representation['created_at'] = changed_format_datetime_c 
        representation['updated_at'] = changed_format_datetime_u

        # representation['is_grouped_by_tracking_code'] = True

        return representation
       

class QrcodeInfoSerializer(serializers.Serializer):
    tracking_code = serializers.CharField(max_length=13)
    id_number = serializers.CharField(max_length=60)
    size = serializers.CharField(max_length=10)
    logo = serializers.URLField(max_length=300, allow_null=True, allow_blank=True,required=False)
    qr_code = serializers.CharField(allow_blank=True, trim_whitespace=True)
    sender_address = serializers.CharField()
    sender_name = serializers.CharField()
    sender_phone = serializers.CharField()
    sender_plaque = serializers.CharField()
    sender_unity = serializers.CharField()
    # sender_state = serializers.CharField()
    sender_zone = serializers.CharField()

    receiver_address = serializers.CharField()
    receiver_name = serializers.CharField()
    receiver_phone = serializers.CharField()
    receiver_plaque = serializers.CharField()
    receiver_unity = serializers.CharField()
    # receiver_state = serializers.CharField()
    receiver_zone = serializers.CharField()
    
    pickup_date = serializers.CharField()
    pickup_time = serializers.CharField()
    delivery_time = serializers.CharField()
    بزرگ = serializers.IntegerField(default=0)
    متوسط = serializers.IntegerField(default=0)
    کوچک = serializers.IntegerField(default=0)
    address_description = serializers.CharField(allow_blank=True, allow_null=True)
    # def to_representation(self, instance):
    #     # Call the base class implementation
    #     data = super().to_representation(instance)
        
    #     # Check if instance is a dict and then update with extra fields
    #     if isinstance(instance, dict):
    #         extra_fields = {k: v for k, v in instance.items() if k not in self.fields}
    #         print(f"Extra fields being added: {extra_fields}")  # Debugging to check extra fields
    #         data.update(extra_fields)
        
    #     return data
    


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
    


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    def clean_value(self, value):
        """Removes asterisks and trims whitespace from strings."""
        if isinstance(value, str):
            return value.replace('*', '').strip()
        return value

    def create_orders_from_excel(self, validated_data):
        user = self.context['request'].user
        excel_file = validated_data['file']
        process = ProcessExcel.objects.filter(user=user)
        if process:
            process.delete()
        process = ProcessExcel.objects.create(user=user, count=0)
        # Read the Excel file using pandas
        df = pd.read_excel(excel_file)
        df.rename(columns=lambda col: col.replace('*', '').strip(), inplace=True)
        count_of_excel = df.shape[0]
        print(count_of_excel)
        orders_created = []
        errors = []
        not_fill_flag = False
        use_receiver_address = False
        use_sender_address = False
        order_number_check = False
        all_rows_empty = True
        tracking_codes = set()
        flag_for_process = True
        required_columns = [
        "شناسه کسب و کار", "تعداد بسته‌ی کوچک", "تعداد بسته‌ی متوسط", "تعداد بسته‌ی بزرگ",
        "محتوا", "ارزش(تومان)", "سرویس", "تاریخ جمع آوری", "عنوان آدرس فرستنده",
        "نام فرستنده", "شماره فرستنده", "پلاک فرستنده", "واحد فرستنده",
        "عنوان آدرس گیرنده", "نام گیرنده", "شماره گیرنده", "پلاک گیرنده",
        "واحد گیرنده",
        ]
        required_receiver_address = [
            "لت گیرنده", "لانگ گیرنده"
        ]
        required_sender_address = [
            "لت فرستنده", "لانگ فرستنده"
        ]
        if df.empty:
            errors.append(f"تمام ردیف‌ها : فایل خالی است")
        else:
            for index, row in df.iterrows():
                index_count = index + 2
                process.count += 100/int(count_of_excel)
                if flag_for_process:
                    process.count =process.count - 100/int(count_of_excel)
                    flag_for_process = False
                process.save()
                if index > 0:  # Skip the first row (index 0)
                    # Check if all columns in the current row are empty
                    if row.isnull().all():
                        if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                            errors.append(f"ردیف {index_count}: ردیف خالی است")
                        continue
                try:
                    
                    row = row.apply(self.clean_value)
                    for col in required_columns:
                        if pd.isnull(row.get(col)):
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: فیلد '{col}' نمی‌تواند خالی باشد.")
                            not_fill_flag = True
                        if not_fill_flag:
                            break 

                    for col in required_receiver_address:
                        if pd.isnull(row.get(col)):
                            use_receiver_address = True
                            if pd.isnull(row['آدرس گیرنده']):
                                if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                    errors.append(f"ردیف {index_count}: آدرس یا(لت و لانگ) گیرنده باید پر باشد")
                                not_fill_flag = True
                        if not_fill_flag:
                            break
                        
                    for col in required_sender_address:
                        if pd.isnull(row.get(col)):
                            use_sender_address = True
                            if pd.isnull(row['آدرس فرستنده']):
                                if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                    errors.append(f"ردیف {index_count}: آدرس یا(لت و لانگ) فرستنده باید پر باشد")
                                not_fill_flag = True
                        if not_fill_flag:
                            break



                    
                    small_size_count = row['تعداد بسته‌ی کوچک']
                    medium_size_count = row['تعداد بسته‌ی متوسط']
                    big_size_count = row['تعداد بسته‌ی بزرگ']
                    size_list = [{'کوچک':small_size_count}, {'متوسط':medium_size_count}, {'بزرگ':big_size_count}]
                    if small_size_count==0 and medium_size_count==0 and big_size_count==0:
                        if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                            errors.append(f"ردیف {index_count}:حداقل یکی ازفیلدهای تعداد بسته ها باید غیر صفر باشد")
                        continue
                    if small_size_count == 0:
                        size_list.remove({'کوچک':small_size_count})
                    if medium_size_count == 0:
                        size_list.remove({'متوسط':medium_size_count})
                    if big_size_count == 0:
                        size_list.remove({'بزرگ':big_size_count})
                    service = Service.objects.filter(title=row['سرویس']).first()
                    if not service:
                        if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                            errors.append(f"ردیف {index_count}:  سرویس یافت نشد")
                        continue
                    business = Business.objects.filter(id=row['شناسه کسب و کار']).first()
                    if service.is_private:
                        related_businesses = list(service.business.all())  # Retrieve the list of related businesses
                        if business not in related_businesses:  # Check if the given business is in the list
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}:  این سرویس برای بیزینس تعیین شده نمی باشد")
                            continue
                    today_gregorian = datetime.datetime.now().date()
                    today_datetime = str(jdatetime.date.fromgregorian(date=today_gregorian)).replace('-', '/')
                    today_datetime = english_to_persian_number(today_datetime)
                    pickup_date_ex = english_to_persian_number(row['تاریخ جمع آوری'])
                    if pickup_date_ex.replace(" ", "") == today_datetime:
                        request_time = datetime.datetime.now()
                        if request_time.time() >= service.hour:
                            bus_id = row['شناسه کسب و کار']
                            if (bus_id=='C3YS' and service.id == '10L9' and request_time.time() <= datetime.time(9, 15, 0)):
                                pass
                            elif (bus_id=='C3YS' and service.id == 'C7HI' and request_time.time() <= datetime.time(14, 30, 0)):
                                pass
                            else:    
                                if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                    errors.append(f"ردیف {index_count}:زمان انتخاب این سرویس گذشته است ")
                                continue
                    #check Thirsday for evening service
                    # if row['سرویس'] == 'سرویس درون شهری - عصرگاهی':
                    #     if is_thursday(pickup_date_ex):
                    #         if not any(error.startswith(f"ردیف {index + 1}:") for error in errors):
                    #             errors.append(f"ردیف {index + 1}:این سرویس در روزهای پنجشنبه فعال نیست")
                    #         continue

                    #check holidays
                    # try:
                    #     english_pickup_date = persian_to_english_number(pickup_date_ex)
                    #     url = f'https://holidayapi.ir/jalali/{english_pickup_date}'
                    #     response = requests.get(url, timeout=10)  # Add a timeout for safety
                    #     response.raise_for_status()  # Raise HTTP errors
                    #     data = response.json()
                    #     if data.get('is_holiday') == True:
                    #         if not any(error.startswith(f"ردیف {index + 1}:") for error in errors):
                    #             errors.append(f"ردیف {index + 1}:تاریخ انتخابی تعطیل است")
                    #         continue
                    # except requests.exceptions.RequestException as e:
                    #     # Handle network or HTTP errors
                    #     # errors.append(f"ردیف {index + 1}:خطا در بررسی تعطیلات ({str(e)})")
                    #     # continue
                    #     pass

                    for size_d in size_list:
                        if use_receiver_address == False:
                        # Extract sender and receiver information
                            
                            receiver_lat = row['لت گیرنده'][0] if isinstance(row['لت گیرنده'], tuple) else row['لت گیرنده']
                            receiver_long = row['لانگ گیرنده'][0] if isinstance(row['لانگ گیرنده'], tuple) else row['لانگ گیرنده']
                        else:
                            try:
                                receiver_lat = get_location(f'تهران، {row["آدرس گیرنده"]}')['location']['y']
                                receiver_long = get_location(f'تهران، {row["آدرس گیرنده"]}')['location']['x']
                            except:
                                receiver_lat= rayan_data['lat']
                                receiver_long= rayan_data['lng']
                            
                        if use_sender_address == False:
                            sender_lat = row['لت فرستنده'][0] if isinstance(row['لت فرستنده'], tuple) else row['لت فرستنده']
                            sender_long = row['لانگ فرستنده'][0] if isinstance(row['لانگ فرستنده'], tuple) else row['لانگ فرستنده']
                        else:
                            try:
                                sender_lat = get_location(f'تهران، {row["آدرس فرستنده"]}')['location']['y']
                                sender_long = get_location(f'تهران، {row["آدرس فرستنده"]}')['location']['x']
                            except:
                                sender_lat= rayan_data['lat']
                                sender_long= rayan_data['lng']    
                        try:
                            sender_data = get_geolocation(sender_lat, sender_long)
                        except:
                            sender_data= rayan_data
                            sender_lat= rayan_data['lat']
                            sender_long= rayan_data['lng']
                        
                        try:
                            receiver_data = get_geolocation(receiver_lat, receiver_long)
                        except:
                            receiver_data= rayan_data
                            receiver_lat= rayan_data['lat']
                            receiver_long= rayan_data['lng']
                        # Lookup related objects (like Business, City, State, etc.)
                        business = Business.objects.filter(id=row['شناسه کسب و کار']).first()
                        if not business:
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: کسب و کار با آیدی {row['شناسه کسب و کار']}  یافت نشد.")
                            continue  # Skip to the next row
                        # Access the related CustomUser through the business (assuming there's a OneToOne or ForeignKey relationship)
                        business_user = business.legal_profile.user_admin if business.legal_profile else business.real_profile.user
                        if user != business_user:
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: کاربر اجازه ثبت سفارش با این کسب و کار را ندارد.")
                            continue
                                        
                        # Retrieve the Wallet associated with the CustomUser
                        wallet = Wallet.objects.get(user=user)
                        sender_city = City.objects.filter(name=sender_data['city']).first()
                        sender_state = State.objects.filter(name=sender_data['state'].replace("استان", "").strip()).first()
                        receiver_city = City.objects.filter(name=receiver_data['city']).first()
                        receiver_state = State.objects.filter(name=receiver_data['state'].replace("استان", "").strip()).first()
                        # If city/state is not found, log the error and continue
                        if not sender_city or not sender_state:
                            # if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                            #     errors.append(f"ردیف {index_count}:فرمت آدرس فرستنده صحیح نیست")
                            # continue
                            sender_data= rayan_data
                            sender_city = rayan_data['city_id']
                            sender_state = rayan_data['state_id']
                            
                        if not receiver_city or not receiver_state:
                            receiver_data= rayan_data
                            receiver_city = rayan_data['city_id']
                            receiver_state = rayan_data['state_id']

                        package = Package.objects.filter(title='بسته').first()                      
                        content = Content.objects.filter(title=row['محتوا']).first()
                        service = Service.objects.filter(title=row['سرویس']).first()
                        # max_value = int(re.findall(r'\d+', row['ارزش'])[0])
                        # value = Value.objects.filter(max_value=max_value).first()
                        value = row['ارزش(تومان)']
                        # If any critical fields are missing, log the error and skip the row
                        if not package :
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}:بسته یافت نشد")
                            continue

                        if not content :
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: محتوا یافت نشد")
                            continue

                        if not service:
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: سرویس یافت نشد")
                            continue
                        
                        if not value:
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: ارزش یافت نشد")
                            continue

                        receiver_phone=row['شماره گیرنده']
                        receiver_name=row['نام گیرنده']
                        receiver_phone = f'0{receiver_phone}'
                        count_box = 0 
                        flag_for_wallet_less = False
                        decrease_count = 0
                        # Generate unique tracking code
                        orders = Order.objects.filter(user_business=business,
                                                    receiver_lat=receiver_lat,
                                                    receiver_long=receiver_long,
                                                    receiver_phone=receiver_phone,
                                                    receiver_name=receiver_name,
                                                    sender_lat=sender_lat,
                                                    sender_long=sender_long,
                                                    pickup_date=pickup_date_ex,
                                                    service__id=service.id,
                                                    pursuit__in=["waiting for payment", "waiting for collection"],
                                                    value=value,
                                                    pre_order=0)
                        
                        size_title = next(iter(size_d))
                        if size_title:
                            orders_rep = orders.filter(size__title=size_title)
                        else:
                            # Handle case where size_d is empty or doesn't have a valid title
                            orders_rep = orders.none()
                        size = Size.objects.filter(title=size_title).first()
                        count_box_new = size_d[size_title]
                        if count_box_new == 0:
                            continue
                        if orders_rep:
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}:(در بخش داشبورد سفارش های خود را چک کنید) سفارشی کاملا مشابه این ردیف از قبل ثبت شده است و در انتظار جمع آوری یا در انتظار پرداخت است")
                                continue
                        if orders:
                            tracking_code = orders.first().tracking_code
                            delivery_code = orders.first().delivery_code
                            order_number = orders.first().order_number
                            flag_for_count = True
                            order_number_check = True
                            # Calculate price and total price
                            for order in orders:
                                count_box += order.count

                            previous_total_price = orders.order_by('created_at').last().total_price
                            service_price = service.price
                            size_price = float(size.price_co) * service_price
                            # count_box_new = int(row['تعداد'])
                            if count_box == 0:
                                count_box = count_box_new
                            else:
                                count_box += count_box_new
                            if count_box >= 2:
                                decrease_count = count_box_new
                            price = ((int(service_price) + float(size_price)) * int(count_box_new))-((float(service_price)+(float(get_object_or_404(Size, title='کوچک').price_co) * int(service_price)))*decrease_count*0.3)
                            
                            # check if counts are ok  
                            # n1= n2= n3= 0
                            # for order in orders:
                            #     if order.size.title == 'بزرگ':
                            #         n1 += int(order.count)
                            #     elif order.size.title == 'متوسط':
                            #         n2 += int(order.count)
                            #     elif order.size.title == 'کوچک':
                            #         n3 += int(order.count) 
                            # big_n, medium_n, small_n = 0, 0, 0
                            # if size_title == 'بزرگ':
                            #     big_n = n1 + count_box_new
                            # elif size_title == 'متوسط':
                            #     medium_n = n2 + count_box_new
                            # elif size_title == 'کوچک':
                            #     small_n = n3 + count_box_new
                            # if can_fit(big_n, medium_n, small_n):
                                #allocation
                            pickup_date = None
                            flag = True
                            last_order = orders.order_by('created_at').last()
                            pickup_date = last_order.pickup_date
                            # pickup_time1 = last_order.service.pickup_time
                            dispatcher_sender = last_order.dispatcher_sender
                            dispatcher_receiver = last_order.dispatcher_reciever
                            # zone = last_order.receiver_zone
                            service = last_order.service
                            
                            # all_orders_for_this_dispatcher = Order.objects.filter(dispatcher_sender_id=disp_receiver.id, 
                            #                                                             pickup_date=pickup_date,
                            #                                                             service=service,
                            #                                                             service__pickup_time=pickup_time1).all()
                            # small, medium, big = small_n, medium_n, big_n
                            # for order in all_orders_for_this_dispatcher:
                            #     if order.tracking_code == orders.last().tracking_code:
                            #         continue
                            #     if order.size.title == 'کوچک':
                            #         small += order.count
                            #     elif order.size.title == 'متوسط':
                            #         medium += order.count
                            #     elif order.size.title == 'بزرگ':
                            #         big += order.count
                            # if can_fit(big,medium,small):
                            
                            if wallet.amount < (price + (price * tax_co)):
                                if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                    errors.append(f"ردیف {index_count}: هزینه سفارش بیشتر از موجودی کیف پول است")
                                continue
                                
                            amount = price + (price * tax_co)
                            wallet.amount -= amount
                            #increase wallet charge for every payment
                            wallet_co = get_object_or_404(
                                IncreaseWalletCo
                            )
                            coefficient = float(wallet_co.Coefficient)
                            wallet.amount += amount*coefficient
                            wallet.save()
                            total_price = price * tax_co + price + previous_total_price# Add tax
                            for order in orders:
                                order.dispatcher_sender= dispatcher_sender
                                order.dispatcher_reciever = dispatcher_receiver
                                order.total_price = total_price
                                order.save()
                            flag = False        
                        else:
                            flag_t = True
                            # Generate a unique tracking code
                            while flag_t:
                                letters_first = ''.join(random.choices(string.ascii_uppercase, k=2))
                                letters_last = ''.join(random.choices(string.ascii_uppercase, k=2))

                                # Generate random numbers for the middle part
                                numbers = ''.join(random.choices(string.digits, k=9))

                                # Concatenate the parts to form the code
                                tracking_code = letters_first + numbers + letters_last

                                if not Order.objects.filter(tracking_code=tracking_code).exists():
                                    delivery_code = random.randint(1000, 9999)
                                    if not order_number_check:
                                        order_number = random.randint(1000, 9999)

                                    # Calculate price and total price
                                    service_price = service.price
                                    size_price = float(size.price_co) * service_price
                                    count_box_price = int(count_box_new)
                                    # n1= n2= n3= 0
                                    # if size_title == 'بزرگ':
                                    #     n1 = count_box_new
                                    # elif size_title == 'متوسط':
                                    #     n2 = count_box_new
                                    # elif size_title == 'کوچک':
                                    #     n3 = count_box_new 
                                    # if can_fit(n1, n2, n3):
                                    service_title = row['سرویس']
                                    service_type = Service.objects.filter(title=service_title).first().s_type
                                    pickup_date= english_to_persian_number(row['تاریخ جمع آوری'])
                                    service_count = service.count
                                    check_service_count= CheckServiceCount.objects.filter(
                                        pickup_date=pickup_date,
                                        service_type=service_type, 
                                        service_title=service_title).first()
                                    if check_service_count:
                                        if check_service_count.service_count==0 or service_count==0:
                                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                                errors.append(f"ردیف {index_count}: متاسفانه سرویسی برای این تاریخ وجود ندارد'")
                                            flag_for_wallet_less=True
                                            break
                                    #allocation
                                    pickup_date = english_to_persian_number(row['تاریخ جمع آوری'])
                                    # pickup_time1 = service.pickup_time
                                    # zone = sender_data['municipality_zone']

                                    # dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone__zone_id=zone, service__id=service.id)
                                    # if not dispatchers_in_this_zone.exists():
                                    #     if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                    #         errors.append(f"ردیف {index_count}: متاسفانه سفیری برای منطقه{zone} وجود ندارد'")
                                    #     flag_for_wallet_less=True
                                    #     flag_t=False
                                    #     break
                                    
                                    dispatcher_order_counts = {}
                                    dispatcher_sender_order_counts = {}

                                    
                                    ##allocation
                                    zone = receiver_data['municipality_zone']
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

                                    if count_box_price >= 2:
                                        decrease_count = int(count_box_new)-1
                                    
                                    price = ((int(service_price) + float(size_price)) * int(count_box_new))-((float(service_price)+(float(get_object_or_404(Size, title='کوچک').price_co) * int(service_price)))*decrease_count*0.3)
                                    value = int(value)
                                    if value<1000000 and value>0:
                                        val_price = 2000
                                    elif value>=1000000 and value<=20000000:
                                        val_price = float(value*0.002)
                                    elif value>20000000 and value<=50000000:
                                        val_price=float(value*0.003)
                                    else:
                                        if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                            errors.append(f"ردیف {index_count}: ارزش معتبر نمیباشد")
                                            flag_for_wallet_less = True
                                        break

                                    total_price = price + (val_price)  # Include insurance
                                    total_price += total_price * tax_co  # Add tax
                                    if wallet.amount < (price + (price * tax_co)):
                                        if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                            errors.append(f"ردیف {index_count}: هزینه سفارش بیشتر از موجودی کیف پول است")
                                        flag_for_wallet_less = True
                                        break

                                    wallet_co = get_object_or_404(
                                        IncreaseWalletCo
                                    )
                                    coefficient = float(wallet_co.Coefficient)
                                    wallet.amount -= total_price
                                    wallet.amount += total_price*coefficient
                                    wallet.save()
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

                                    break
                        
                        
                        if flag_for_wallet_less:
                            continue
                        # Create the order
                        if use_sender_address == False:
                            sender_address = sender_data['formatted_address']
                        else:
                            sender_address = row['آدرس فرستنده']
                        if use_receiver_address == False:
                            receiver_address = receiver_data['formatted_address']
                        else:
                            receiver_address = row['آدرس گیرنده']
                        try:
                            order = Order.objects.create(
                                user_business=business,
                                address_description=row['توضیحات آدرس'],
                                package_id=package.id,
                                size_id=size.id,
                                count=count_box_new,
                                content_id=content.id,
                                service_id=service.id,
                                value=value,
                                pickup_date=english_to_persian_number(row['تاریخ جمع آوری']),

                                sender_title=row['عنوان آدرس فرستنده'],
                                sender_state=sender_state,
                                sender_city=sender_city,
                                sender_address=sender_address,
                                sender_zone=sender_data['municipality_zone'],
                                sender_district=sender_data['neighbourhood'],
                                sender_plaque=row['پلاک فرستنده'],
                                sender_unity=row['واحد فرستنده'],
                                sender_name=row['نام فرستنده'],
                                sender_phone=f'0{row["شماره فرستنده"]}',
                                sender_lat=sender_lat,
                                sender_long=sender_long,
                                sender_map_link=f'https://nshn.ir/?lat={sender_lat}&lng={sender_long}',
                                dispatcher_sender=dispatcher_sender,

                                receiver_title=row['عنوان آدرس گیرنده'],
                                receiver_state=receiver_state,
                                receiver_city=receiver_city,
                                receiver_address=receiver_address,
                                receiver_zone=receiver_data['municipality_zone'],
                                receiver_district=receiver_data['neighbourhood'],
                                receiver_plaque=row['پلاک گیرنده'],
                                receiver_unity=row['واحد گیرنده'],
                                receiver_name=row['نام گیرنده'],
                                receiver_phone=f'0{row["شماره گیرنده"]}',
                                receiver_lat=receiver_lat,
                                receiver_long=receiver_long,
                                receiver_map_link=f'https://nshn.ir/?lat={receiver_lat}&lng={receiver_long}',
                                dispatcher_reciever=dispatcher_receiver,

                                price=price,
                                total_price=total_price,
                                tracking_code=tracking_code,
                                delivery_code=delivery_code,
                                pursuit='waiting for collection',
                                payment_status = True,
                                credit = True,
                                payment = 'excel',
                                bank_code = 'excel',
            
                            )

                            orders_created.append(order)
                            tracking_codes.add(tracking_code)
                            
                            # order_created_signal.send(sender=Order)
                        
                        except Exception as e:
                            check_service_count= CheckServiceCount.objects.filter(
                                        pickup_date=pickup_date,
                                        service_type=service_type, 
                                        service_title=service_title).first()
                            check_service_count.service_count += 1
                            check_service_count.save()
                            total_price_deleted = total_price
                            wallet = Wallet.objects.get(user=user)
                            wallet_co = get_object_or_404(
                                                    IncreaseWalletCo
                                                )
                            coefficient = float(wallet_co.Coefficient)
                            price_for_return = total_price_deleted - (total_price_deleted*coefficient)
                            wallet.amount += price_for_return
                            wallet.save()
                            if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                                errors.append(f"ردیف {index_count}: {str(e)}")

                    

                except Exception as e:
                    if not any(error.startswith(f"ردیف {index_count}:") for error in errors):
                        errors.append(f"ردیف {index_count}: {str(e)}")
                    
            if errors:
                total_price_deleted = 0
                for tracking_code in tracking_codes:
                    order = Order.objects.filter(tracking_code=tracking_code).first()
                    check_service_count= CheckServiceCount.objects.filter(
                                    pickup_date=order.pickup_date,
                                    service_type=order.service.s_type, 
                                    service_title=order.service.title).first()
                    check_service_count.service_count += 1
                    check_service_count.save()
                    orders = Order.objects.filter(tracking_code=tracking_code).all()
                    total_price_deleted += orders.last().total_price
                    orders.delete()
                wallet = Wallet.objects.get(user=user)
                wallet_co = get_object_or_404(
                                        IncreaseWalletCo
                                    )
                coefficient = float(wallet_co.Coefficient)
                price_for_return = total_price_deleted - (total_price_deleted*coefficient)
                wallet.amount += price_for_return
                wallet.save()
            else:
                for tracking_code in tracking_codes:
                    orders = Order.objects.filter(tracking_code=tracking_code).all()
                    if not order_number:
                        order_number = random.randint(1000, 9999)
                    for order in orders:
                        order.order_number = order_number
                        order.save()
                orders_count = len(tracking_codes)
                if user.phone is not None:
                    SendExcelOrderSms(f'{user.phone}', orders_count)
                elif user.email is not None:
                    subject = 'ثبت سفارش در رایان'
                    message = f'سفارش شما با موفقیت در رایان ثبت شد. تعداد سفارش: {orders_count}'

                    from_email = settings.EMAIL_HOST_USER  # Change this to your email
                    to_email = user.email

                    send_mail(subject, message, from_email, [to_email])

        return orders_created, errors

    def generate_tracking_code(self):
        while True:
            letters_first = ''.join(random.choices(string.ascii_uppercase, k=2))
            letters_last = ''.join(random.choices(string.ascii_uppercase, k=2))
            numbers = ''.join(random.choices(string.digits, k=9))
            tracking_code = letters_first + numbers + letters_last

            if not Order.objects.filter(tracking_code=tracking_code).exists():
                delivery_code = random.randint(1000, 9999)
                return tracking_code, delivery_code


class ProcessExcelSerializers(serializers.ModelSerializer):
    rounded_count = serializers.IntegerField()  # Add this to handle the annotated field

    class Meta:
        model = ProcessExcel
        fields = ['count', 'rounded_count']

