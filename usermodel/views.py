import random
import jwt
from kavenegar import *
from jose.exceptions import JWTError

from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings

from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken

from business.models import Business
from userprofile.models import LegalUserProfile, RealUserProfile
from config.settings import API_KEY
from core.utils.constant import site

from .serializers import *


class RegisterCodeSend(generics.CreateAPIView):
    serializer_class = RegisterCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            return Response({'message': 'کاربر قبلا ثبت نام کرده است'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        code = random.randint(1000, 9999)
        custom_register_code = CustomRegisterLoginCode.objects.filter(username=username)
        if custom_register_code.exists():
            custom_register_code.delete()

        CustomRegisterLoginCode.objects.create(username=username, code=code)
        if '@' in username:
            # Send the code with email
            subject = 'ورود به رایان'
            message = f'کد ورود رایان: {code}'
            from_email = settings.EMAIL_HOST_USER  # Change this to your email
            to_email = username
            send_mail(subject, message, from_email, [to_email])
        else:
            phone = username
            try:
                api = KavenegarAPI(API_KEY)
                params = {
                    'receptor': f'{phone}',
                    'template': 'verify',
                    'token': f'{code}',
                    'type': 'sms',  # sms vs call
                }
                response = api.verify_lookup(params)
            except APIException as e:
                return Response({'message': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)
            except HTTPException as e:
                return Response({'message': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'کد ورود ارسال شد'}, status=status.HTTP_200_OK)
    

class RegisterCodeDelete(generics.DestroyAPIView):
    serializer_class = RegisterCodeSerializer
    queryset = CustomRegisterLoginCode
    def delete(self, request):
        username = request.POST.get('username')
        code = self.queryset.objects.filter(username=username).all()
        code.delete()
        return Response({'message': 'با موفقیت حذف شد'}, status=status.HTTP_204_NO_CONTENT)


class LoginCodeSend(generics.CreateAPIView):
    serializer_class = LoginCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        if not CustomUser.objects.filter(username=username).exists():
            return Response({'message': 'این کاربر ثبت نام نکرده است'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        code = random.randint(1000, 9999)
        custom_register_code = CustomRegisterLoginCode.objects.filter(username=username)
        if custom_register_code.exists():
            custom_register_code.delete()

        CustomRegisterLoginCode.objects.create(username=username, code=code)
        if '@' in username:
            # Send the code with email
            subject = 'ورود به رایان'
            message = f'کد ورود رایان: {code}'
            from_email = settings.EMAIL_HOST_USER  # Change this to your email
            to_email = username

            send_mail(subject, message, from_email, [to_email])

        else:
            phone = username
            try:
                api = KavenegarAPI(API_KEY)
                params = {
                    'receptor': f'{phone}',
                    'template': 'verify',
                    'token': f'{code}',
                    'type': 'sms',  # sms vs call
                }
                response = api.verify_lookup(params)
            except APIException as e:
                return Response({'message': f'کد ارسال نشد'}, status=status.HTTP_400_BAD_REQUEST)
            except HTTPException as e:
                return Response({'message': f'کد ارسال نشد'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'کد ورود ارسال شد'}, status=status.HTTP_200_OK)    


class CheckRegisterCodeView(APIView):
    def post(self, request, *args, **kwargs):
        username = self.request.data.get('username')
        code = self.request.data.get('code')
        if username is None:
            return Response({'message': 'نام کاربری یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        if code is None:
            return Response({'message': 'کد را وارد کنید'}, status=status.HTTP_400_BAD_REQUEST)

        reg_inf = get_object_or_404(
            CustomRegisterLoginCode,
            username=username
        )
        reg_code = reg_inf.code
        if reg_code == code:
            reg_inf.check_code = True
            reg_inf.save()
            return Response({'message': 'کد صحیح است'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'کد اشتباه است'}, status=status.HTTP_404_NOT_FOUND)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        data_out = {}
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        # email = serializer.validated_data.get('email')
        # phone = serializer.validated_data.get('phone')
        email = None
        phone = None
        if '@' in username:
            email = username
#             subject = 'ورود به رایان'
#             message = f'''
#             کاربر گرامی به رایان پست خوش آمدید! 
# رایان پست، پلتفرم لجستیکی هوشمند کسب‌وکار شماست  
# با استفاده از رایان پست، فرایند ارسال بسته‌های مربوط به کسب‌و‌کار خود را در زمان کم، با هزینه‌ای مقرون‌به‌صرفه و کاملا اختصاصی مدیریت کنید.

# پشتیبانی رایان پست همیشه در کنار شما و پاسخگوی شما خواهد بود. 

# رایان پست 
# همراه کسب‌وکار توست
# '''
#             from_email = settings.EMAIL_HOST_USER  # Change this to your email
#             to_email = username

#             send_mail(subject, message, from_email, [to_email])
        else:
            phone = username
            # try:
            #     api = KavenegarAPI(API_KEY)
            #     params = {
            #             'receptor': f'{phone}',
            #             'template': 'welcome',
            #             'token': 'کاربر',
            #             'type': 'sms',  # sms vs call
            #         }
            #     response = api.verify_lookup(params)
            # except APIException as e:
            #     print({'error': f'{e}'})
            # except HTTPException as e:
            #     print({'error': f'{e}'})

        data_out['email'] = email
        data_out['phone'] = phone
        account = serializer.save()
        refresh = RefreshToken.for_user(account)

        data_out['token'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        data_out['message'] = 'ثبت نام شما با موفقیت انجام شد'
        response = JsonResponse(data_out, status=status.HTTP_201_CREATED)
        
        # response['Authorization'] = f'Bearer {refresh.access_token}'
        # response['Access-Control-Allow-Credentials'] = 'true'
        # response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        # response.set_cookie('Authorization', f'Bearer {refresh.access_token}', httponly=True, secure=True)
        return response


class LoginView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        # phone = request.data.get('phone', None)
        # email = request.data.get('email', None)
        username = request.data['username']
        password = request.data['password']
        email = None
        phone = None
        if '@' in username:
            email = username
        else:
            phone = username
        
        if not CustomUser.objects.filter(username=username).exists():
            return Response({'message': 'این کاربر ثبت نام نکرده است'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        user = authenticate(request, email=email, phone=phone, password=password)
        if user is not None:
            # User is authenticated, generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            data_out = {}
            # Additional response data
            data_out['email'] = email
            data_out['phone'] = phone
            # describe user role
            real = RealUserProfile.objects.filter(user=user).first()
            legal_admin = LegalUserProfile.objects.filter(user_admin=user).first()
            legal_user = LegalUserProfile.objects.filter(user=user).first()
            if real is not None:
                data_out['role'] = real.role
            elif legal_admin is not None:
                data_out['role'] = f'{legal_admin.role} - legal_admin'
            elif legal_user is not None:
                data_out['role'] = f'{legal_user.role} - legal_user'
            else:
                data_out['role'] = ' '
            # tokens
            data_out['token'] = {
                'refresh': str(refresh),
                'access': str(access_token)
            }

            data_out['message'] = 'ورود شما با موفقیت انجام شد'
            response = JsonResponse(data_out, status=status.HTTP_200_OK)

            # response['Authorization'] = f'Bearer {refresh.access_token}'
            # response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            # response['Access-Control-Allow-Credentials'] = 'true'
            #
            # response.set_cookie('Authorization', f'Bearer {refresh.access_token}', httponly=True, secure=True)
            return response
        else:
            # Authentication failed
            return Response({'message': 'نام کاربری یا رمزعبور اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)


class LoginOTPView(generics.CreateAPIView):
    serializer_class =  UserLoginOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        email = None
        phone = None
        if '@' in username:
            email = username
        else:
            phone = username
        user = CustomUser.objects.filter(username=username).first()
        if user is not None:
            # User is authenticated, generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            data_out = {}
            # Additional response data
            data_out['email'] = email
            data_out['phone'] = phone
            # describe user role
            real = RealUserProfile.objects.filter(user=user).first()
            legal_admin = LegalUserProfile.objects.filter(user_admin=user).first()
            legal_user = LegalUserProfile.objects.filter(user=user).first()
            if real is not None:
                data_out['role'] = real.role
            elif legal_admin is not None:
                data_out['role'] = f'{legal_admin.role} - legal_admin'
            elif legal_user is not None:
                data_out['role'] = f'{legal_user.role} - legal_user'
            else:
                data_out['role'] = ' '
            # tokens
            data_out['token'] = {
                'refresh': str(refresh),
                'access': str(access_token)
            }

            data_out['message'] = 'ورود شما با موفقیت انجام شد'
            response = JsonResponse(data_out, status=status.HTTP_200_OK)

            # response['Authorization'] = f'Bearer {refresh.access_token}'
            # response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            # response['Access-Control-Allow-Credentials'] = 'true'
            #
            # response.set_cookie('Authorization', f'Bearer {refresh.access_token}', httponly=True, secure=True)
            return response
        else:
            # Authentication failed
            return Response({'message': 'نام کاربری اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)

TOKEN_BLACKLIST = set()

class CustomTokenRefreshView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = RefreshToken(self.request.data.get('refresh'))
            return Response({
                'access': str(token.access_token),
                             })
        except InvalidToken as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class LogoutView(APIView):
    def post(self, request):
        # token = request.headers.get('Authorization', '').split(' ')[-1]
        token = request.COOKIES.get('Authorization', '').split(' ')[-1]
        try:
            # decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            TOKEN_BLACKLIST.add(token)

            return Response({'detail': 'با موفقیت خارج شدید'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def protected_view(request):
    # Get the token from the request (e.g., from headers)
    token = request.headers.get('Authorization', '').split(' ')[-1]
    # token = request.COOKIES.get('Authorization', '').split(' ')[-1]
    if not token:
        return JsonResponse({'message': 'there isnt any authorization Token'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    try:
        if token in TOKEN_BLACKLIST:
            raise jwt.ExpiredSignatureError('این توکن قبلا استفاده شده و در بلک لیست می باشد')
        # Decode and verify the token
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Access user information from the decoded payload
        # username
        user_id = decoded_payload['user_id']
        user = CustomUser.objects.filter(id=user_id).first()
        username = user.username
        # user information
        real = RealUserProfile.objects.filter(user=user).first()
        real_b = Business.objects.filter(real_profile=real).first()
        legal_admin = LegalUserProfile.objects.filter(user_admin=user).first()
        legal_b = Business.objects.filter(legal_profile=legal_admin).first()
        legal_user = LegalUserProfile.objects.filter(user=user).first()
        if user.groups.exists():
            is_admin=True
        else:
            is_admin=False

        business_count = 0
        
        # Check if the user has exactly one business
        one_business = business_count == 1

        flag = False
        role = ' '
        phone = ''
        first_name = ''
        last_name = ''
        company_name = ''
        image = ''
        bus_id = ''
        flag_b = False
        user_id = user_id
        is_admin = is_admin

        if legal_admin is not None:
            flag = True
            role = f'{legal_admin.role} - legal_admin'
            phone = legal_admin.phone
            company_name = legal_admin.company_name
            if legal_admin.logo:
                image = site + legal_admin.logo.url
            if legal_b:
                flag_b = True
                business = Business.objects.filter(legal_profile=legal_admin)
                business_count = business.count()
                if business_count == 1:
                    bus_id = business.first().id

        # elif legal_user is not None:
        #     flag = True
        #     role = f'{legal_user.role} - legal_user'
        #     phone = legal_user.phone
        #     company_name = legal_user.company_name
        #     if legal_user.logo:
        #         image = site + legal_user.logo.url
        elif real is not None:
            flag = True
            role = real.role
            phone = real.phone_number
            first_name = real.first_name
            last_name = real.last_name
            if real.image:
                image = site + real.image.url
            if real_b:
                flag_b = True
                business = Business.objects.filter(legal_profile=legal_admin)
                business_count = business.count()
                if business_count == 1:
                    bus_id = business.first().id

        return JsonResponse(
            {
                'username': username,
                'flag': flag,
                'role': role,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'company_name': company_name,
                'image': image,
                'flag_b': flag_b,
                'user_id': user_id,
                'bus_id': bus_id,
                'is_admin': is_admin,

            }, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        # Handle token expiration
        return JsonResponse({'error': 'Token has expired'}, status=401)
    except JWTError:
        # Handle other JWT errors
        return JsonResponse({'error': 'Invalid token'}, status=401)


class ActivateUserView(APIView):
    def get(self, request):
        user = request.user
        if user.is_active:
            user.is_active = False
            user.save()
        else:
            user.is_active = True
            user.save()
        return Response({'message': 'فعال بودن کاربر تغییر کرد'}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = CustomUser
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordCodeSend(generics.CreateAPIView):
    serializer_class = ForgotPasswordSerializer

    def create(self, request, *args, **kwargs):
        username = request.data['username']

        # Look up the user by email (adjust as needed for your user model)
        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user:
            code = random.randint(1000, 9999)
            reset_user = CustomResetPassword.objects.filter(user=user)
            if reset_user:
                reset_user.delete()

            CustomResetPassword.objects.create(user=user, code=code)
            if '@' in username:
                # Send the password reset email
                subject = 'بازیابی رمز عبور'
                message = (f'کد بازیابی رمز عبور رایان: {code}')
                from_email = settings.EMAIL_HOST_USER  # Change this to your email
                to_email = user.email

                send_mail(subject, message, from_email, [to_email])

            else:
                phone = username
                try:
                    api = KavenegarAPI(API_KEY)
                    params = {
                        'receptor': f'{phone}',
                        'template': 'forgetpassword',
                        'token': f'{code}',
                        'type': 'sms',  # sms vs call
                    }
                    response = api.verify_lookup(params)
                except APIException as e:
                    return Response({'message': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)
                except HTTPException as e:
                    return Response({'message': f'{e}'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'message': 'کد بازیابی ارسال شد'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordCodeDelete(generics.DestroyAPIView):
    serializer_class = ForgotPasswordSerializer
    queryset = CustomResetPassword
    def delete(self, request):
        username = request.data['username']

        # Look up the user by email (adjust as needed for your user model)
        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if user:
            code = self.queryset.objects.filter(user=user).all()
            code.delete()
            return Response({'message': 'با موفقیت حذف شد'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class CheckResetPasswordCodeView(APIView):
    def post(self, request, *args, **kwargs):
        username = self.request.data.get('username')
        code = self.request.data.get('code')
        if username is not None:
            username = request.data['username']
        else:
            return Response({'message': 'نام کاربری یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        if code is not None:
            code = request.data['code']
        else:
            return Response({'message': 'کد را وارد کنید'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(
            CustomUser,
            username=username
        )

        reset_inf = get_object_or_404(
            CustomResetPassword,
            user=user
        )
        reset_code = reset_inf.code
        if reset_code == code:
            reset_inf.check_code = True
            reset_inf.save()
            return Response({'message': 'کد صحیح است'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'کد بازیابی اشتباه است'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(generics.CreateAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        username = self.request.data.get('username')
        if username is not None:
            username = request.data['username']
        else:
            return Response({'message': 'نام کاربری یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(
            CustomUser,
            username=username
        )
        reset_inf = get_object_or_404(
            CustomResetPassword,
            user=user
        )
        if reset_inf.check_code == True:
            user.set_password(password)
            user.save()
            reset_inf.delete()
            return Response({'message': 'رمز عبور با موفقیت تغییر کرد'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': ' کد بازیابی تایید نشده است'}, status=status.HTTP_404_NOT_FOUND)


from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView): # if you want to use Authorization Code Grant, use this
    adapter_class = GoogleOAuth2Adapter
    # callback_url = "rayanpost.ir/"
    callback_url = "http://localhost:3000/"
    client_class = OAuth2Client