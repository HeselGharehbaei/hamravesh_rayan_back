from django.urls import path
from .views import *
urlpatterns = [
    path('wallet/', WalletListView.as_view()),
    path('add-bank-account/', AddBankAccount.as_view()),
    path('see-bank-account/', SeeBankAccount.as_view()),
    path('find-id-bank/', FindIdBank.as_view()),
    path('pay-out/', PayOutAdd.as_view()),
    path('daily-wallet/', DailyWalletListView.as_view())

]