from django.test import TestCase
from dispatcher_payment.views import allocation2

tracking_code = 'DH610598654NT'
allocation2(tracking_code)