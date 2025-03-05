from django.urls import path
from .views import *

urlpatterns = [
    path('enter/code/', EnterCodeSend.as_view()),
    path('delete/code/', DeleteCustomCode.as_view()),
    path('enter/', UserEnterView.as_view()),
    path('verify/', protected_view),
    path('logout/', LogoutView.as_view()),
    path('active/', ActivateUserView.as_view()),
    path('dashboard/', DashboardInfo.as_view(),)
]