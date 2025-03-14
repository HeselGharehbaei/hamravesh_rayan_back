import random
from django.forms import model_to_dict
import jwt
from core.utils.constant import site as siteb
from django.core.mail import send_mail
from kavenegar import *
from jose.exceptions import JWTError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import api_view

from dispatcher_vehicle.models import DispatcherVehicle
from .permission import IsAuthenticatedWithToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from dispatcher_profile.models import DispatcherProfile
from config.settings import API_KEY


class EnterCodeSend(generics.CreateAPIView):
    serializer_class = DispatcherEnterCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        code = random.randint(1000, 9999)
        custom_register_code = DispatcherEnterCode.objects.filter(username=username)
        if custom_register_code.exists():
            custom_register_code.delete()

        DispatcherEnterCode.objects.create(username=username, code=code)
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


class DeleteCustomCode(generics.DestroyAPIView):
    serializer_class = DispatcherEnterCodeSerializer
    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        custom_register_code = DispatcherEnterCode.objects.filter(username=username)
        if custom_register_code.exists():
            custom_register_code.delete()
            return Response({'message': 'با موفقیت حذف شد'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message':'کد برای کاربر وجود ندارد'}, status=status.HTTP_400_BAD_REQUEST)

class UserEnterView(generics.CreateAPIView):
    serializer_class = DispatcherEnterSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        # password = request.data.get('password')
        user = Dispatcher.objects.filter(username=username).first()
        if user:
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            data_out = {
                'username': username,
                'role': 'dispatcher',
                'token': {
                    'refresh': str(refresh),
                    'access': str(access_token)
                },
                'message': 'ورود شما با موفقیت انجام شد'
            }
            return JsonResponse(data_out, status=status.HTTP_200_OK)
        else:            
            data_out = {}
            phone = username
            data_out['phone'] = phone
            account = serializer.save()
            refresh = RefreshToken.for_user(account)

            data_out['token'] = {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
            data_out['message'] = 'ثبت نام شما با موفقیت انجام شد'
            response = JsonResponse(data_out, status=status.HTTP_201_CREATED)
            return response

TOKEN_BLACKLIST = set()


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
    if not token:
        return JsonResponse({'message': 'there isnt any authorization Token'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    try:
        if token in TOKEN_BLACKLIST:
            raise jwt.ExpiredSignatureError('این توکن قبلا استفاده شده و در بلک لیست می باشد')
        # Decode and verify the token
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Access user information from the decoded payload
        user_id = decoded_payload['user_id']
        user = Dispatcher.objects.filter(id=user_id).first()
        username = user.username

        # complete and confirm profile or not
        profile = DispatcherProfile.objects.filter(user__id=user_id).first()
        profile_complete = False
        profile_confirm = False
        has_shaba = False
        if profile is not None:
            if profile.shaba_number is not None:
                has_shaba = True
            if profile.confirm == True:
                profile_confirm = True

            profile_dict = model_to_dict(profile)

            # Fields to exclude from the completeness check
            excluded_fields = ['shaba_number', 'expiration_certificate_date', 'education', 'role', 'description','zone', 'service', 'confirm', 'birth_certificate_no', 'certificate_no', 'phone_number', 'postal_code']

            # Check if all required fields (except excluded) are filled
            all_filled = all(
                value is not None for key, value in profile_dict.items() if key not in excluded_fields
            )

            profile_complete = all_filled
        
        #complete vehicle or not
        vehicle = DispatcherVehicle.objects.filter(dispatcher__id=user_id).first()
        vehicle_complete = False
        if vehicle is not None:
            vehicle_dict = model_to_dict(vehicle)

            # Fields to exclude from the completeness check
            excluded_fields = ['new_plaque', 'plaque', 'confirm', 'vehicle_documents', 'motorcycle_type', 'insurance_no', 'insurance_image', 'expiration_insurance_date']

            # Check if all required fields (except excluded) are filled
            all_filled2 = all(
                value is not None for key, value in vehicle_dict.items() if key not in excluded_fields
            )

            vehicle_complete = all_filled2
        
        return JsonResponse(
            {
                'username': username,
                'role': 'dispatcher',
                'phone': username,
                'user_id': user_id,
                'profile_complete': profile_complete,
                'profile_confirm': profile_confirm,
                'vehicle_complete': vehicle_complete,
                'has_shaba': has_shaba,

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

class DashboardInfo(APIView):
    def get(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        if not token:
            return JsonResponse({'message': 'there isnt any authorization Token'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            if token in TOKEN_BLACKLIST:
                raise jwt.ExpiredSignatureError('این توکن قبلا استفاده شده و در بلک لیست می باشد')
            # Decode and verify the token
            decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            # Access user information from the decoded payload
            user_id = decoded_payload['user_id']
            profile = DispatcherProfile.objects.filter(user_id=user_id).first()
            vehicle = DispatcherVehicle.objects.filter(dispatcher_id=user_id).first()
            if profile is None or vehicle is None:
                return Response({'message': 'کاربر پروفایل یا وسیله نقلیه ندارد'}, status=status.HTTP_404_NOT_FOUND)
            data = {
            'first_name' : profile.first_name,
            'last_name' : profile.last_name,
            'phone_number' : profile.phone_number,
            'image' : f'{siteb}{profile.image.url}',
            'vehicle' : vehicle.get_vehicle_display_translated(),
            'motorcycle_type' : vehicle.motorcycle_type,
            'plaque' : vehicle.plaque
            }
            return Response(data, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
        # Handle token expiration
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except JWTError:
        # Handle other JWT errors
            return JsonResponse({'error': 'Invalid token'}, status=401)


nathional_code_city = [
169,170,149,150,171,168,136,137,138,545,505,636,164,165,172,623,506,519,154,155,567,173,159,160,604,274,275,295,637,292,492,289,677,294,493,279,280,288,284,285,638,291,640,293,675,282,
283,286,287,296,297,290,400,401,404,405,397,398,399,647,502,584,402,403,392,393,395,396,386,387,503,444,551,447,561,445,718,'083',446,448,552,543,442,443,'051','052','053','058',
'055',617,'057',618, '059','060','061','062',544,'056',571,593,667,348,586,338,339,343,344,346,337,554,469,537,345,470,341,342,483,484,557,418,416,417,412,413,592,612,613,406,
407,421,598,419,385,420,528,213,214,205,206,498,568,711,217,218,221,582,483,625,576,578,227,208,209,225,577,712,215,216,626,627,579,713,499,222,219,220,500,501,623,497,223,689,
487,226, 224,486,211,212,628,202,203,531,488,261,273,630,264,518,631,258,259,570,265,268,269,653,517,569,267,262,263,593,266,693,271,272,694,270,516,333,334,691,323,322,595,
395,641,596,336, 335,496,337,324,325,394,330,332,331,687,422,423,599,600,688,424,425,426,550,697,384,377,378,558,385,646,375,376,372,373,379,380,383,674,381,382,676,722,542,
312,313,317,310,311,302,303,583,321,382,304,305,536,605,308,309,306,307,319,313,314,606,320,698,298,299,535,315,316,318,607,608,508,538,728,509,438,439,580,590,559,588,431,432,
'037','038',702,240,241,670,648,252,678,253,649,513,546,671,246,247,654,548,547,655,248,249,253,514,665,673,228,229,230,679,256,257,244,245,681,723,236,237,683,656,250,251,515,
242,243,238,239,657,255, 684,700,642,457,456,458,459,460,530,520,358,359,682,703,364,365,371,701,720,366,367,704,361,362,369,370,635,668, 533,705,699,669,725,597,611,525,181,
527,585,685,663,192-193,174,175,183,184,481,706,194,195,185,186,182	,199,200,198,662,190,191,692,189,707,526,187,188,729,730,196,197,661,680,643,562,572,'074',644,'072','073',
'069','070', 521,573,522,724,'076','077',650,574,'078','079','081','084',651,'086','087','089','090',553,'091','092','093','094','097', '098','096',105,106,'063','067','068',
'075',591,'082',635,524, 468,465,461,462,467,632,555,633,629,466,696,721,'064','065',523,652,719,716,'085','088',563,529,353,349,350,355,609,351,352,354,732,357,532,610,356,556,
658,'001','002','003','004','005','006','007','008','011','020','025','015','043',666,489,'044','045','048','049',490,491,695,659,'031','032',664,717,'041','042',471,472,454,581,
449,450,616,534,455,451,726,634,453,727,452,145,146,731,690,601,504,163,714,715,566,166,167,161,162,686,603,619,118,127,128,129,620,621,549,564,575,113,114,122,540,660,120,512,510,
511,119,115,112,110,111,125,126,565,121,116,117,541,622,124,108,109,123,428,427,507,158,615,152,153
]

