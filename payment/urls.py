from django.urls import path
from .views import *

urlpatterns = [
    # path('credit/new/', CreditCreateView.as_view()),
    path('credit/', CreditListView.as_view()),
    # path('wallet/new/', WalletCreateView.as_view()),
    path('wallet/', WalletListView.as_view()),
]