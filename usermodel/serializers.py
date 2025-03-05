import datetime
import jdatetime
from django.core.mail import send_mail
from kavenegar import *
from django.db import IntegrityError
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from payment.models import Wallet, Credit, GiveWalletCharge
from config import settings
from .models import *
# from dispatcher.models import Dispatcher
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from core.utils.validations import username_validate_for_users

def gregorian_to_jalali(gregorian_date):
    """Convert a Gregorian date to a Jalali (Persian) date."""
    jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
    formatted_jalali_date = str(jalali_date).replace('-', '/')
    return formatted_jalali_date

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    username = serializers.CharField()

    class Meta:
        model = CustomUser
        exclude = ('email', 'phone')

    # def validate_username(self, username):    
    #     return username_validate_for_users(username)           

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')

        if password != password2:
            raise serializers.ValidationError("تکرار رمزعبور صحیح نیست")

        # Use Django's built-in password validation
        validate_password(password)

        #validate username
        username = data.get('username')

        # if '@' in username:
        #     if not email_validator(username):
        #         raise serializers.ValidationError({'username': _('ایمیل معتبر وارد کنید')}, code='invalid')
        if not '@' in username:
            if not re.match(phone_pattern_iran, username):
                raise serializers.ValidationError({'username': _('شماره معتبر وارد کنید(حتما در ابتدای شماره صفر قرار دهید)')}, code='invalid')

        return data

    def create(self, validated_data):
        password = validated_data.get('password', None)
        validated_data.pop('password2', None)
        username = validated_data.get('username')
        current_date = datetime.datetime.now().date()
        current_date = gregorian_to_jalali(current_date)

        phone = None
        email = None
        if '@' in username:
            email = username
        else:
            phone = username
        # if email is None and phone is not None:
        reg = CustomRegisterLoginCode.objects.filter(username=username).first()
        if not reg:
            raise serializers.ValidationError("کد تایید وارد نشده")
        if not reg.check_code:
            raise serializers.ValidationError("کد تایید وارد نشده")

        reg.delete()
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("این نام کاربری قبلا ثبت شده است")

            # Create user
        try:
            user = CustomUser.objects.create_user(username=username, password=password, email=email, phone=phone)
        except IntegrityError:
            # Handle IntegrityError (e.g., username already exists)
            raise serializers.ValidationError("Failed to create user.")

        amount = 0
        give_charge = GiveWalletCharge.objects.all()
        if give_charge:
            matching_charge = give_charge.filter(
                start_date__lte=current_date,
                finish_date__gte=current_date
            ).first()
            if matching_charge:
                amount=matching_charge.amount
            
        Wallet.objects.create(user=user, amount=amount)
        Credit.objects.create(user=user, amount=0)
        
        if '@' in username:
            email = username
            subject = 'ورود به رایان'
            message = f'''
            کاربر گرامی به رایان پست خوش آمدید! 
            رایان پست، پلتفرم لجستیکی هوشمند کسب‌وکار شماست  
            با استفاده از رایان پست، فرایند ارسال بسته‌های مربوط به کسب‌و‌کار خود را در زمان کم، با هزینه‌ای مقرون‌به‌صرفه و کاملا اختصاصی مدیریت کنید.
            پشتیبانی رایان پست همیشه در کنار شما و پاسخگوی شما خواهد بود. 
            رایان پست 
            همراه کسب‌وکار توست
            '''
            from_email = settings.EMAIL_HOST_USER  # Change this to your email
            to_email = username
            send_mail(subject, message, from_email, [to_email])
        else:
            phone = username
            try:
                pass
                # api = KavenegarAPI(settings.API_KEY)
                # params = {
                #         'receptor': f'{phone}',
                #         'template': 'welcome',
                #         'token': 'کاربر',
                #         'type': 'sms',  # sms vs call
                #     }
                # response = api.verify_lookup(params)
            except APIException as e:
                print({'error': f'{e}'})
            except HTTPException as e:
                print({'error': f'{e}'})
        return user


class UserLoginOTPSerializer(serializers.Serializer):
    username = serializers.CharField()
    code= serializers.CharField()

    def validate(self, data):
        # total validation
        username = data.get('username')
        # Check if the username exists
        if not CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("این نام کاربری ثبت نشده است")     
        code = data.get('code')
        #check code
        if code is None:
            raise serializers.ValidationError({'message': 'کد را وارد کنید'})
        reg_inf = CustomRegisterLoginCode.objects.filter(username=username).first()
        # Check if the code exists in the record and code not exists in database
        if not reg_inf and code!=None:
            raise serializers.ValidationError({'message': 'کد اشتباه است'})
        if not reg_inf:
            raise serializers.ValidationError("کد تایید وارد نشده")
        elif not reg_inf.code == code:
            raise serializers.ValidationError({'message': 'کد اشتباه است'})
        # Delete the registration code after validation
        reg_inf.delete()
        return data      


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class ChangePasswordSerializer(serializers.Serializer):
  model = CustomUser

  """
  Serializer for password change endpoint.
  """
  old_password = serializers.CharField(required=True)
  new_password = serializers.CharField(required=True)


class ForgotPasswordSerializer(serializers.ModelSerializer):
    username= serializers.CharField(write_only=True)
    class Meta:
        model = CustomResetPassword
        fields = '__all__'



class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')

        if password != password2:
            raise serializers.ValidationError("تکرار رمزعبور صحیح نیست")

        # Use Django's built-in password validation
        validate_password(password)
        return data


class RegisterCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRegisterLoginCode
        fields = '__all__'


    def validate_username(self, username):    
        return username_validate_for_users(username)        


class LoginCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRegisterLoginCode
        fields = '__all__'
        