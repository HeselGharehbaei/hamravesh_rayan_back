import os
import jdatetime
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.files import File
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from usermodel.models import CustomUser
from userprofile.models import RealUserProfile
from business.models import BusinessType, Business
from unittest.mock import patch
from .models import PaymentAmount
from options.models import(
    Size, 
    Package, 
    Service, 
    Value, 
    Content,
    CheckServiceCount
)
from order.models import Order
from cities.models import (
    City, 
    State, 
    District
)
from payment.models import(
    Wallet,
    CreditCo,
    IncreaseWalletCo,
) 
site = 'http://subtest.rayanpost.ir'


class BaseTestSetup(APITestCase):

    def setUp(self) -> None: 
        """
        Create a new object of order to testing payment api
        """
        # Create user and profile
        self.user= CustomUser.objects.create(
            username= 'hgharehbaai@gmail.com', 
            password= 'h0e9s8e7l6'
        )
        self.profile = RealUserProfile.objects.create(
            user=self.user, 
            address='gomishan', 
            first_name='hesel', 
            last_name='gharehbaei'
        )
        
        # Create business type and business
        self.business_type = BusinessType.objects.create(title='poshak')
        self.user_business = Business.objects.create(
            real_profile=self.profile, 
            name='ibolak', 
            b_type=self.business_type
        )
        
        # Create user wallet and CreditCo
        self.user_wallet = Wallet.objects.create(
            user=self.user, 
            amount=30000
        )
        CreditCo.objects.create(coefficient=0.1)
        self.coe= IncreaseWalletCo.objects.create(Coefficient=0.02)
        # Generate access and refresh tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.order_wallet_url = reverse('request_order_wallet')
        self.content = Content.objects.create(title='شکستنی')
        self.service = Service.objects.create(
            title='ارسال فوری', 
            pickup_time='8-4', 
            delivery_time='14-18', 
            price=10, 
            s_type='درون شهری'
        )
        self.state = State.objects.create(name='Tehran')
        self.city = City.objects.create(name='Tehran')
        self.district = District.objects.create(name='District 1')
        self.state.city.add(self.city)
        self.city.district.add(self.district)
        # Create size, package, value, service, state, city, and district
        self.value= Value.objects.create()
        self.create_common_data()        
        # Create orders
        self.create_orders()

    def create_common_data(self):
        # Path to the sample image file
        image_path = os.path.join(os.path.dirname(__file__), 'test_image.jpg')
        
        # Check if the file exists
        self.assertTrue(os.path.exists(image_path), f"Sample image file does not exist at {image_path}")
        
        # Create size instances
        self.size_small = Size.objects.create(
            title='کوچک', 
            description='small', 
            price_co=10
        )
        self.size_medium = Size.objects.create(
            title='متوسط', 
            description='medium', 
            price_co=20
        )
        self.size_big = Size.objects.create(
            title='بزرگ', 
            description='big', 
            price_co=30
        )

        # Create package instance
        with open(image_path, 'rb') as image_file:
            self.package = Package.objects.create(
                title='Test Package',
                short_description='Short description for test package',
                description='Detailed description for test package',
                icon=File(image_file, name='test_image.jpg')
            )
            
            # Assign sizes to the package
            self.package.size.set([self.size_small, self.size_medium, self.size_big])
                
        # Check if the instance was created successfully
        self.assertIsNotNone(self.package.id, "Failed to create Package instance")
        self.assertTrue(self.package.icon, "Icon field is empty in Package instance")
        self.assertIn('icons/test_image', self.package.icon.name, "Icon file path does not match")
    
    def create_orders(self):
        tomorrow_gregorian = datetime.now() + timedelta(days=1)
        tomorrow_jalali = jdatetime.date.fromgregorian(date=tomorrow_gregorian)
        pickup_date = tomorrow_jalali.strftime('%Y-%m-%d')

        def create_order(pre_order, size, count, tracking_code):
            return Order.objects.create(
                pre_order=pre_order, 
                user_business=self.user_business, 
                order_description='Sample order description',
                address_description='Sample address description', 
                package=self.package, 
                size=size, 
                count=count,
                content=self.content, 
                service=self.service, 
                value=self.value, 
                pickup_date=pickup_date,
                sender_address='Sample sender address', 
                sender_plaque='1', sender_stage='1', 
                sender_state=self.state,
                sender_city=self.city, 
                sender_district=self.district, 
                sender_unity='1', 
                sender_name='Sample Sender',
                sender_phone='09120000000', 
                receiver_address='Sample receiver address', 
                receiver_plaque='1',
                receiver_stage='1', 
                receiver_unity='1', 
                receiver_state=self.state, 
                receiver_city=self.city,
                receiver_district=self.district, 
                receiver_name='Sample Receiver', 
                receiver_phone='09120000001',
                price=2, 
                total_price=1000, 
                pursuit='waiting for payment', 
                bank_code='1234567890123456',
                tracking_code=tracking_code, 
                payment_status=False, 
                payment='Online', 
                credit=False, 
                dispatcher=None
            )
        
        self.order_small = create_order(1, self.size_small, 2, 'AB123456789CD')
        self.order_medium = create_order(1, self.size_medium, 1, self.order_small.tracking_code)
        self.order_big = create_order(0, self.size_big, 0, self.order_small.tracking_code)
   

class PaymentSetUp(BaseTestSetup):

    def test_valid_send_request_order_wallet(self):
        """
        Test sending a valid request to the order wallet API.
        """
        # Store the initial service count (if it exists)
        initial_service_count = CheckServiceCount.objects.filter(
            pickup_date=self.order_small.pickup_date,
            service_type=self.order_small.service.s_type,
            service_title=self.order_small.service.title
        ).first()
        
        initial_count = initial_service_count.service_count if initial_service_count else None

        # Send request to the API
        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('کد پیگیری', response.data['message'])

        # Check if the CheckServiceCount instance for the pickup date and service type is created or updated
        service_count_instance = CheckServiceCount.objects.filter(
            pickup_date=self.order_small.pickup_date,
            service_type=self.order_small.service.s_type,
            service_title=self.order_small.service.title
        ).first()
        
        self.assertIsNotNone(service_count_instance)

        # If the instance existed before, check that the service count is decremented by one
        if initial_count is not None:
            self.assertEqual(service_count_instance.service_count, initial_count - 1)
        else:
            # If a new instance was created, check that the service count is decremented by one from the order's service count
            expected_count = self.order_small.service.count - 1
            self.assertEqual(service_count_instance.service_count, expected_count)

    def test_invalid_user_id(self):
        """
        Test sending a request with an invalid user ID.
        """
        response = self.client.get(self.order_wallet_url, {'id': 99999, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data['message'], 'کاربر یافت نشد')

    def test_no_orders_found(self):
        """
        Test sending a request with a tracking code that does not match any orders.
        """
        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code':""})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_not_enough_wallet_balance(self):
        """
        Test sending a request when the user does not have enough wallet balance.
        """
        self.user_wallet.amount = 0
        self.user_wallet.save()
        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'موجودی کیف پول کافی نمی باشد')

    def test_wallet_not_found(self):
        """
        Test sending a request when the user's wallet does not exist.
        """
        self.user_wallet.delete()
        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'کیف پول موجود نمی باشد')

    def test_successful_payment_and_wallet_update(self):
        """
        Test a successful payment and wallet balance update.
        """
        initial_wallet_balance = self.user_wallet.amount
        order_total_price = self.order_small.total_price

        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('کد پیگیری', response.data['message'])

        # Refresh wallet and order instances from the database
        self.user_wallet.refresh_from_db()
        self.order_small.refresh_from_db()

        self.assertEqual(self.user_wallet.amount, initial_wallet_balance - order_total_price * (1 - 0.02))
        self.assertTrue(self.order_small.payment_status)
        self.assertEqual(self.order_small.bank_code, 'wallet')
        self.assertEqual(self.order_small.payment, 'Transaction success')
        self.assertEqual(self.order_small.pursuit, 'waiting for collection')
        self.assertTrue(self.order_small.credit)

    def test_no_service_for_date(self):
        # Create a CheckServiceCount instance with service_count set to 0
        CheckServiceCount.objects.create(
            pickup_date=self.order_small.pickup_date,
            service_type=self.order_small.service.s_type,
            service_title=self.order_small.service.title,
            service_count=0
        )

        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'متاسفانه سرویسی برای این تاریخ وجود ندارد')

    def test_package_count_exceeds_limit(self):
        # Update counts to not be within limits
        self.order_big.count = 10
        self.order_big.save()
        self.order_medium.count = 5
        self.order_medium.save()
        self.order_small.count = 8
        self.order_small.save()
        response = self.client.get(self.order_wallet_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'تعداد بسته‌های انتخابی بیش از حد مجاز است')  


class SendRequestWalletTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.client = APIClient()
        self.client.login(username='testuser', password='12345')
        self.url = reverse('send_request_wallet')
        self.amount = 1000  # مقدار تست

    @patch('requests.post')
    def test_send_request_wallet_success(self, mock_post):
        mock_response = {
            "data": {"authority": "test_authority"},
            "errors": []
        }
        mock_post.return_value.json.return_value = mock_response
        response = self.client.get(self.url, {'amount': self.amount})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(PaymentAmount.objects.filter(user=self.user, amount=self.amount*10).exists())

    @patch('requests.post')
    def test_send_request_wallet_failure(self, mock_post):
        mock_response = {
            "data": {},
            "errors": {"code": 101, "message": "Invalid request"}
        }
        mock_post.return_value.json.return_value = mock_response
        response = self.client.get(self.url, {'amount': self.amount})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Error code: 101, Error Message: Invalid request', response.content.decode())

    def test_send_request_wallet_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.url, {'amount': self.amount})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('کاربر لاگین نیست', response.content.decode())


class VerifyWalletTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.client = APIClient()
        self.client.login(username='testuser', password='12345')
        self.url = reverse('verify_wallet')
        self.payment_amount = PaymentAmount.objects.create(user=self.user, amount=10000, tracking_code='wallet', authority='test_authority')
        self.wallet = Wallet.objects.create(user=self.user, amount=0)

    @patch('requests.post')
    def test_verify_wallet_success(self, mock_post):
        mock_response = {
            "data": {"code": 100, "ref_id": "test_ref_id"},
            "errors": []
        }
        mock_post.return_value.json.return_value = mock_response
        response = self.client.get(self.url, {'Status': 'OK', 'Authority': 'test_authority'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_amount.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertTrue(self.payment_amount.payment_status)
        self.assertEqual(self.wallet.amount, 1100)  # 1000/10 + 10% بیشتر

    @patch('requests.post')
    def test_verify_wallet_failure(self, mock_post):
        mock_response = {
            "data": {},
            "errors": {"code": 101, "message": "Invalid request"}
        }
        mock_post.return_value.json.return_value = mock_response
        response = self.client.get(self.url, {'Status': 'OK', 'Authority': 'test_authority'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Error code: 101, Error Message: Invalid request', response.content.decode())

    def test_verify_wallet_payment_not_found(self):
        response = self.client.get(self.url, {'Status': 'OK', 'Authority': 'invalid_authority'})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertIn('خطایی اتفاق افتاده', response.content.decode())

    def test_verify_wallet_canceled(self):
        response = self.client.get(self.url, {'Status': 'NOK', 'Authority': 'test_authority'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Transaction failed or canceled by user', response.content.decode())



class SendRequestOrderTest(BaseTestSetup):

    def setUp(self):
        super().setUp()  # Call the base class setup
        self.send_request_order_url = reverse('send_request_order')

    @patch('requests.post')
    def test_send_request_order_success(self, mock_post):
        mock_response = {
            "data": {"authority": "test_authority"},
            "errors": []
        }
        mock_post.return_value.json.return_value = mock_response

        response = self.client.get(self.send_request_order_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(PaymentAmount.objects.filter(user=self.user, amount=self.order_small.total_price * 10).exists())

    @patch('requests.post')
    def test_send_request_order_failure(self, mock_post):
        mock_response = {
            "data": {},
            "errors": {"code": 101, "message": "Invalid request"}
        }
        mock_post.return_value.json.return_value = mock_response

        response = self.client.get(self.send_request_order_url, {'id': self.user.id, 'tracking_code': self.order_small.tracking_code})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Error code: 101, Error Message: Invalid request', response.content.decode())

    def test_send_request_order_user_not_found(self):
        response = self.client.get(self.send_request_order_url, {'id': '9999', 'tracking_code': self.order_small.tracking_code})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, f'{site}/order/payment', fetch_redirect_response=False)

    def test_send_request_order_no_orders(self):
        response = self.client.get(self.send_request_order_url, {'id': self.user.id, 'tracking_code': 'invalid_tracking_code'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Order not found', response.content.decode())


class VerifyOrderTest(BaseTestSetup):

    def setUp(self):
        super().setUp()  # Call the base class setup
        self.verify_order_url = reverse('verify_order')
        self.amount = 10000
        self.payment_amount = PaymentAmount.objects.create(
            user=self.user, 
            amount=self.amount, 
            tracking_code=self.order_small.tracking_code, 
            authority='test_authority'
        )

    @patch('requests.post')
    def test_verify_order_success(self, mock_post):
        mock_response = {
            "data": {"code": 100, "ref_id": "test_ref_id"},
            "errors": []
        }
        mock_post.return_value.json.return_value = mock_response

        response = self.client.get(self.verify_order_url, {'Status': 'OK', 'Authority': 'test_authority'})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.payment_amount.refresh_from_db()
        self.assertTrue(self.payment_amount.payment_status)
        coefficient = float(self.coe.Coefficient)
        wallet_amount= self.user_wallet.amount
        expected_wallet_amount= wallet_amount + (self.amount/10*coefficient)
        self.user_wallet.refresh_from_db()
        # اطمینان از محاسبه صحیح        
        self.assertAlmostEqual(self.user_wallet.amount, expected_wallet_amount)

    @patch('requests.post')
    def test_verify_order_failure(self, mock_post):
        mock_response = {
            "data": {},
            "errors": {"code": 101, "message": "Invalid request"}
        }
        mock_post.return_value.json.return_value = mock_response

        response = self.client.get(self.verify_order_url, {'Status': 'OK', 'Authority': 'test_authority'})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # self.assertIn('Error code: 101, Error Message: Invalid request', response.content.decode())

    def test_verify_order_payment_not_found(self):
        response = self.client.get(self.verify_order_url, {'Status': 'OK', 'Authority': 'invalid_authority'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('خطایی اتفاق افتاده', response.content.decode())

    def test_verify_order_canceled(self):
        response = self.client.get(self.verify_order_url, {'Status': 'NOK', 'Authority': 'test_authority'}, follow=True)

        # Print response content to understand the cause of the error
        print("Response Content:", response.content.decode())

        # Check for additional debug information
        if response.status_code == 400:
            print("Debug Info:", response.content.decode())

        # Verify the HTTP status code for successful request
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the response content contains the expected message
        self.assertIn('Transaction failed or canceled by user', response.content.decode())
        
        # Check that the order's payment field was updated correctly
        self.order_small.refresh_from_db()
        self.assertEqual(self.order_small.payment, 'Transaction failed or canceled by user')
        
        # Verify the redirection to the correct URL
        self.assertRedirects(response, f'{site}/order/payment/failed', fetch_redirect_response=False)