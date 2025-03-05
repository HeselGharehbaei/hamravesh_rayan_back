import random
import jdatetime
import requests
import re

from django.db import models
from datetime import datetime, time
from django.db.models import Sum
from django.utils.timezone import now, localtime, make_aware

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, APIView
from rest_framework.response import Response

from config.settings import API_KEY, zarinpal_access_token
from order.models import Order
from dispatcher_profile.models import DispatcherProfile
from cities.tests import district_list
from prices.views import can_fit
from .models import Wallet, SettelmentWallet
from .serializers import WalletSerializers

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

        # Return None or an appropriate message if the pattern does not match
    return "Pattern not found" 


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


class WalletListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get current time and convert to Jalali
        local_now = localtime(now())
        jalali_date = jdatetime.datetime.fromgregorian(datetime=local_now)

        # Get the start of the current Jalali month
        jalali_month_start = jdatetime.datetime(jalali_date.year, jalali_date.month, 1)

        # Calculate the end of the Jalali month
        if jalali_date.month == 12:  # If Esfand (last month), next month is Farvardin of the next year
            jalali_month_end = jdatetime.datetime(jalali_date.year + 1, 1, 1)
        else:
            jalali_month_end = jdatetime.datetime(jalali_date.year, jalali_date.month + 1, 1)

        # Convert Jalali dates to Gregorian for database filtering
        month_start = make_aware(jalali_month_start.togregorian())
        month_end = make_aware(jalali_month_end.togregorian())
        print((month_start, month_end))
        
        # Filter records where created_at is in the current Persian month
        total_amount = SettelmentWallet.objects.filter(
            user=user,
            created_at__range=(month_start, month_end)
        ).aggregate(total=Sum('amount'))['total'] or 0
        print(total_amount)
        results = [{
            "persian_month": jalali_date.strftime("%B"),  # Current Persian month name
            "amount": round(total_amount)
        }]
        return Response({'results':results}, status=status.HTTP_200_OK)
        

    

class DailyWalletListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # دریافت زمان کنونی بر اساس تهران
        local_now = localtime(now())

        # محاسبه‌ی شروع و پایان روز به وقت تهران
        today_start = make_aware(datetime.combine(local_now.date(), time(0, 0, 0, 0)))
        today_end = make_aware(datetime.combine(local_now.date(), time(23, 59, 59, 999999)))

        # محاسبه مجموع مقدار پولی که امروز اضافه شده است
        total_amount_today = SettelmentWallet.objects.filter(
            user=user,
            created_at__range=(today_start, today_end)
        ).aggregate(total=models.Sum('amount'))['total'] or 0  # اگر مقدار None باشد، مقدار 0 برگردانده شود.

        total_amount_today= round(total_amount_today)
        return Response({"total_amount_today": total_amount_today})


# @api_view(['POST'])
def allocation(tracking_code):
    # tracking_code = request.POST.get('tracking_code')
    
    # if not tracking_code:
    #     return Response({'message': 'Tracking code is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    orders = Order.objects.filter(tracking_code=tracking_code)
    
    if not orders.exists():
        return Response({'message':'No orders found for the given tracking code.'}, status=status.HTTP_404_NOT_FOUND)

    # count = 0
    district = None
    pickup_date = None

    small_n,medium_n,big_n = 0, 0, 0
    for order in orders:
        if order.size.title == 'کوچک':
            small_n += order.count
        elif order.size.title == 'متوسط':
            medium_n += order.count
        elif order.size.title == 'بزرگ':
            big_n += order.count
        else:
            return Response({'message':'عنوان سایز در سفارش ها یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        district = order.sender_district.name.strip()
        pickup_date = order.pickup_date
        pickup_time1 = order.service.pickup_time
        disp = order.dispatcher_sender
    
    if disp is not None:
        return Response({'message': 'سفارش از قبل تخصیص داده شده'}, status=status.HTTP_202_ACCEPTED)

    # Find out which zone the district belongs to
    key = None
    for k, v in district_list.items():
        if district in v:
            key = k
            break
    if key:
        zone = key
    else:
        return Response({'message': f'The district {district} is not found in the dictionary.'}, status=status.HTTP_404_NOT_FOUND)
    
    dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone=zone)
    
    if not dispatchers_in_this_zone.exists():
        return Response({'message': f'No dispatchers found for zone {zone}.'}, status=status.HTTP_404_NOT_FOUND)
    
    dispatcher_order_counts = {}

    # Count unique tracking codes for each dispatcher by pickup_date
    for dispatcher in dispatchers_in_this_zone:
        order_count = dispatcher.dispatcher_sender.filter(
            pickup_date=pickup_date
        ).values('tracking_code').distinct().count()
        dispatcher_order_counts[dispatcher.id] = order_count
    not_fit_key = []
    flag = True
    while flag:
        if not_fit_key:
            for key in not_fit_key:
                del dispatcher_order_counts[key]
                not_fit_key.remove(key)

        if len(dispatcher_order_counts) == 0:
            free_dispatcher_id = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first().id
            small_count, medium_count, large_count = 0, 0, 0
            for order in orders:
                if order.size.title == 'کوچک':
                    small_count = order.count
                elif order.size.title == 'متوسط':
                    medium_count = order.count
                elif order.size.title == 'بزرگ':
                    large_count = order.count
                pickup_date = order.pickup_date
                pickup_time = order.service.pickup_time
                pickup_time = transform_time_range(pickup_time)
                order.dispatcher_sender = DispatcherProfile.objects.filter(id=free_dispatcher_id).first()
                order.dispatcher_reciever = DispatcherProfile.objects.filter(id=free_dispatcher_id).first()
                order.save()
            count = f'{small_count}کوچک/{medium_count}متوسط/{large_count}بزرگ'
            SendFreeDispatcher('09226547417', tracking_code, count, pickup_date, pickup_time)

            return Response({'message': 'سفارش به رای پیک آزاد تخصیص داده شد'}, status=status.HTTP_200_OK)
        else:
            min_value = min(dispatcher_order_counts.values())

            # Find all keys that have the minimum value
            min_keys = [key for key, value in dispatcher_order_counts.items() if value == min_value]

            # Randomly select one of the keys with the minimum value
            selected_key = random.choice(min_keys)
            all_orders_for_this_dispatcher = Order.objects.filter(dispatcher_sender_id=selected_key, 
                                                                  pickup_date=pickup_date,
                                                                  service__pickup_time=pickup_time1).all()
            small, medium, big = small_n, medium_n, big_n
            for order in all_orders_for_this_dispatcher:
                if order.size.title == 'کوچک':
                    small += order.count
                elif order.size.title == 'متوسط':
                    medium += order.count
                elif order.size.title == 'بزرگ':
                    big += order.count
                else:
                    return Response({'message':'عنوان سایز در سفارش ها یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
                    
            if can_fit(big,medium,small):
                for order in orders:
                    order.dispatcher_sender = DispatcherProfile.objects.filter(id=selected_key).first()
                    order.dispatcher_reciever = DispatcherProfile.objects.filter(id=selected_key).first()
                    order.save()
                flag = False
            else:
                not_fit_key.append(selected_key)
        

    return Response({'message': 'با موفقیت افزوده شد'}, status=status.HTTP_200_OK)

def allocation2(tracking_code):
    orders = Order.objects.filter(tracking_code=tracking_code)
    
    if not orders.exists():
        return {'status': False, 'message':'No orders found for the given tracking code.'}

    district = None
    pickup_date = None

    small_n, medium_n, big_n = 0, 0, 0
    for order in orders:
        if order.size.title == 'کوچک':
            small_n += order.count
        elif order.size.title == 'متوسط':
            medium_n += order.count
        elif order.size.title == 'بزرگ':
            big_n += order.count
        else:
            return {'status': False, 'message':'عنوان سایز در سفارش‌ها یافت نشد'}
        district = order.sender_district.name.strip()
        pickup_date = order.pickup_date
        pickup_time1 = order.service.pickup_time
        disp = order.dispatcher_sender

    if disp is not None:
        return {'status': False, 'message': 'سفارش از قبل تخصیص داده شده'}

    # Find the zone for the district
    zone = None
    for k, v in district_list.items():
        if district in v:
            zone = k
            break
    
    if not zone:
        return {'status': False, 'message': f'منطقه {district} یافت نشد'}

    # Find dispatchers in the relevant zone
    dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone=zone)
    
    if not dispatchers_in_this_zone.exists():
        return {'status': False, 'message': f'پیک‌هایی برای منطقه {zone} یافت نشد'}

    dispatcher_order_counts = {}

    # Count orders per dispatcher
    for dispatcher in dispatchers_in_this_zone:
        order_count = dispatcher.dispatcher_sender.filter(
            pickup_date=pickup_date
        ).values('tracking_code').distinct().count()
        dispatcher_order_counts[dispatcher.id] = order_count

    not_fit_key = []
    flag = True

    while flag:
        if not_fit_key:
            for key in not_fit_key:
                del dispatcher_order_counts[key]
                not_fit_key.remove(key)

        if len(dispatcher_order_counts) == 0:
            free_dispatcher_id = DispatcherProfile.objects.filter(first_name='آزاد_سیستم').first().id
            small_count, medium_count, large_count = 0, 0, 0
            for order in orders:
                if order.size.title == 'کوچک':
                    small_count = order.count
                elif order.size.title == 'متوسط':
                    medium_count = order.count
                elif order.size.title == 'بزرگ':
                    large_count = order.count
                pickup_time = transform_time_range(order.service.pickup_time)
                order.dispatcher_sender = DispatcherProfile.objects.filter(user__id=free_dispatcher_id).first()
                order.dispatcher_reciever = DispatcherProfile.objects.filter(user__id=free_dispatcher_id).first()
                order.save()
            count = f'{small_count}کوچک/{medium_count}متوسط/{large_count}بزرگ'
            SendFreeDispatcher('09226547417', tracking_code, count, pickup_date, pickup_time)

            return {'status': True, 'message': 'سفارش به پیک آزاد تخصیص داده شد'}
        else:
            min_value = min(dispatcher_order_counts.values())
            min_keys = [key for key, value in dispatcher_order_counts.items() if value == min_value]
            selected_key = random.choice(min_keys)

            all_orders_for_this_dispatcher = Order.objects.filter(
                dispatcher_sender__user_id=selected_key, 
                pickup_date=pickup_date,
                service__pickup_time=pickup_time1
            ).all()

            small, medium, big = small_n, medium_n, big_n
            for order in all_orders_for_this_dispatcher:
                if order.size.title == 'کوچک':
                    small += order.count
                elif order.size.title == 'متوسط':
                    medium += order.count
                elif order.size.title == 'بزرگ':
                    big += order.count
                else:
                    return {'status': False, 'message': 'عنوان سایز در سفارش‌ها یافت نشد'}

            if can_fit(big, medium, small):
                for order in orders:
                    order.dispatcher_sender = DispatcherProfile.objects.filter(user__id=selected_key).first()
                    order.dispatcher_reciever = DispatcherProfile.objects.filter(user__id=selected_key).first()
                    order.save()
                flag = False
            else:
                not_fit_key.append(selected_key)

    return {'status': True, 'message': 'با موفقیت افزوده شد'}


import requests
class ZarinpalAPI:
    def __init__(self):
        self.url = "https://next.zarinpal.com/api/v4/graphql/"
        token = zarinpal_access_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  # Token authentication
        }

    def add_cart(self, iban, is_legal=False, account_type="SHARE"):
        mutation = """
        mutation BankAccountAdd($iban: String!, $is_legal: Boolean!, $type: BankAccountTypeEnum) {
            BankAccountAdd(iban: $iban, is_legal: $is_legal, type: $type) {
                id
                iban
                name
                status
                type
                is_legal
                holder_name
                issuing_bank {
                    name
                    slug
                }
                expired_at
                deleted_at
            }
        }
        """

        variables = {
            "iban": iban,
            "is_legal": is_legal,
            "type": account_type
        }

        payload = {
            "query": mutation,
            "variables": variables
        }

        response = requests.post(self.url, json=payload, headers=self.headers)
        print(response.text)

        if response.status_code == 200:
            data = response.json()
            return 'با موفقیت افزوده شد', 200, data
        else:
            return f"Failed to execute mutation. Status code: {response.status_code}", response.status_code, response.text
        

    def fetch_bank_accounts(self, limit=200):
        query = f"""
        query {{
            BankAccounts(limit: {limit}) {{
                id
                iban
                holder_name
            }}
        }}
        """
        
        payload = {
            "query": query
        }

        response = requests.post(self.url, json=payload, headers=self.headers)

        if response.status_code == 200:
            return response.json()  # Return the JSON response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def find_id_bank(self, limit=200):
        query = f"""
        query {{
            Terminals(limit: {limit}) {{
                id
                domain
            }}
        }}
        """
        
        payload = {
            "query": query
        }

        response = requests.post(self.url, json=payload, headers=self.headers)

        if response.status_code == 200:
            return response.json()  # Return the JSON response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def payout_add(self, terminal_id, bank_account_id, amount, description=None, reconciliation_parts=None):
        # Define the GraphQL mutation
        mutation = """
        mutation PayoutAdd($terminal_id: ID!, $bank_account_id: ID!, $amount: BigInteger!, $description: String, $reconciliation_parts: ReconciliationPartsEnum) {
          resource: PayoutAdd(terminal_id: $terminal_id, bank_account_id: $bank_account_id, amount: $amount, description: $description, reconciliation_parts: $reconciliation_parts) {
            reconciliation_parts
            id
            url_code
            description
            status
            amount
            percent
            created_at
            updated_at
          }
        }
        """

        # Prepare the variables for the mutation
        variables = {
            "terminal_id": terminal_id,
            "bank_account_id": bank_account_id,
            "amount": amount,
            "description": description,
            "reconciliation_parts": reconciliation_parts
        }

        # Create the payload
        payload = {
            "query": mutation,
            "variables": variables
        }

        try:
            # Send the POST request to Zarinpal's GraphQL endpoint
            response = requests.post(self.url, json=payload, headers=self.headers)

            # Check for a successful response
            if response.status_code == 200:
                return response.json()  # Return the parsed JSON response
            else:
                return {"error": f"Error: {response.status_code} - {response.text}"}

        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, etc.
            return {"error": f"Request failed: {str(e)}"}
terminal_id = "450513"
bank_account_id = "793062"
class AddBankAccount(APIView):
    def post(self, request, *args, **kwargs):
        # Get the IBAN from the request body
        iban = request.data.get('iban')

        if not iban:
            return Response({"error": "IBAN is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize the Zarinpal API class with your token
        zarinpal_api = ZarinpalAPI()

        # Call the add_cart method to add the IBAN
        message, status_code, data = zarinpal_api.add_cart(iban)

        if status_code == 200:
            # Return success response with the data
            return Response({"message": message, "data": data}, status=status.HTTP_200_OK)
        else:
            # Return error response if the mutation fails
            return Response({"error": message, "details": data}, status=status_code)
        

class SeeBankAccount(APIView):
    def get(self, request, *args, **kwargs):
        zarinpal_api = ZarinpalAPI()

        # Fetch bank accounts
        bank_accounts = zarinpal_api.fetch_bank_accounts()

        if bank_accounts:
            return Response(bank_accounts, status=status.HTTP_200_OK)
        else:
            return Response(
                {'message': 'Failed to fetch bank accounts'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class FindIdBank(APIView):
    def get(self, request, *args, **kwargs):
        zarinpal_api = ZarinpalAPI()

        # Fetch bank accounts
        bank_id = zarinpal_api.find_id_bank()

        if bank_id:
            return Response(bank_id, status=status.HTTP_200_OK)
        else:
            return Response(
                {'message': 'Failed to fetch bank accounts'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PayOutAdd(APIView):
    def post(self, request, *args, **kwargs):
        # terminal_id = request.data.get('terminal_id')
        terminal_id = "450513"
        # bank_account_id = request.data.get('bank_account_id')
        bank_account_id = "793062"
        amount = request.data.get('amount')
        # description = request.data.get('description', None)  # Optional description
        description = 'پرداخت تسهیم'
        # reconciliation_parts = request.data.get('reconciliation_parts', None)
        reconciliation_parts = 'MULTI'

        if not amount:
            return Response({"error": "amount required"}, status=status.HTTP_400_BAD_REQUEST)
        
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
            return Response({
                "error": "Failed to add payout", 
                "details": result.get("error", "Unknown error") if result else "Unknown error"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the response contains the expected data
        if "data" in result and "resource" in result["data"]:
            return Response({
                "message": "Payout successfully added", 
                "data": result["data"]["resource"]
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Failed to add payout", 
                "details": result.get("errors", "Unknown error")
            }, status=status.HTTP_400_BAD_REQUEST)


# def AddCart(iban):
#     # Define the API URL
#     url = "https://next.zarinpal.com/api/v4/graphql/"

#     # Set your headers (add authentication token if needed)
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": zarinpal_access_token
#     }

#     # Define the GraphQL mutation and variables
#     mutation = """
#     mutation BankAccountAdd($iban: String!, $is_legal: Boolean!, $type: BankAccountTypeEnum) {
#         BankAccountAdd(iban: $iban, is_legal: $is_legal, type: $type) {
#             id
#             iban
#             name
#             status
#             type
#             is_legal
#             holder_name
#             issuing_bank {
#                 name
#                 slug
#             }
#             expired_at
#             deleted_at
#         }
#     }
#     """

#     # Define the variables for the mutation
#     variables = {
#         "iban": iban,
#         "is_legal": False,  # or False based on your data
#         "type": "SHARE"  # e.g., PERSONAL, BUSINESS
#     }

#     # Create the request payload
#     payload = {
#         "query": mutation,
#         "variables": variables
#     }

#     # Make the POST request
#     response = requests.post(url, json=payload, headers=headers)

#     # Handle the response
#     if response.status_code == 200:
#         # Successful response
#         data = response.json()
#         return 'با موفقیت افزوده شد', 200, data
#     else:
#         # Error occurred
#         return f"Failed to execute mutation. Status code: {response.status_code}",