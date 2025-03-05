from django.urls import path

from .views import *

urlpatterns = [
    path('<str:tracking_code>/', FactorView.as_view()),
    path('multi/<str:order_number>/', FactorMultiView.as_view()),
]
