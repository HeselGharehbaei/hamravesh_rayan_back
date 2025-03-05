from django.urls import path
from .api_views import *
urlpatterns = [
    path('pricing/', PricingAPIView.as_view()),
]