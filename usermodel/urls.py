from django.urls import path
from .views import *

urlpatterns = [
    path('register/code/', RegisterCodeSend.as_view()),
    path('register/code/delete/', RegisterCodeDelete.as_view()),
    path('login/OTP/code/', LoginCodeSend.as_view()),
    path('register/check-code/', CheckRegisterCodeView.as_view()),
    path('register/', UserRegistrationView.as_view()),
    path('refresh/', CustomTokenRefreshView.as_view()),
    path('login/', LoginView.as_view()),
    path('login/OTP/', LoginOTPView.as_view()), 
    path('login/google/', GoogleLogin.as_view()),
    path('verify/', protected_view),
    path('logout/', LogoutView.as_view()),
    path('active/', ActivateUserView.as_view()),
    path('change/password/', ChangePasswordView.as_view()),
    #reset password
    path('reset/code/', ResetPasswordCodeSend.as_view(), name='forgot_password'),
    path('reset/code/delete/', ResetPasswordCodeDelete.as_view()),
    path('reset/check-code/', CheckResetPasswordCodeView.as_view(), name='check-code'),
    path('reset-password/', ResetPasswordView.as_view(), name='password_reset_complete'),
]
