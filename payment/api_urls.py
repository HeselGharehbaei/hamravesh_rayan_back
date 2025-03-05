from django.urls import path
from . import api_views

urlpatterns = [
    #zarinpal
    path('request/order/', api_views.send_request_order, name='send_request_order'),
    path('verify/order/', api_views.verify_order, name='verify_order'),
    #saman
    path('saman/request/order/', api_views.send_request_order_saman, name='send_request_order_saman'),
    path('saman/verify/order/', api_views.verify_order_saman, name='verify_order_saman'),

    path('request/order/wallet/', api_views.send_request_order_wallet, name='request_order_wallet'),
    path('request/wallet/', api_views.send_request_wallet, name='send_request_wallet'),
    path('verify/wallet/', api_views.verify_wallet, name='verify_wallet'),
    #saman wallet
    path('saman/request/wallet/', api_views.send_request_wallet_saman, name='send_request_wallet_saman'),
    path('saman/verify/wallet/', api_views.verify_wallet_saman, name='verify_wallet_saman'),

    path('get-tracking-codes/', api_views.get_tracking_codes, name='get_tracking_codes'),
    # path('test/', api_views.my_view, name='order'),
]