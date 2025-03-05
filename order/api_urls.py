from django.urls import path
from .api_views import *

urlpatterns = [
    path('new/', OrderCreateView.as_view()),
    path('cancel/', CancelOrderView.as_view()),
    path('tracking/', TrackingOrderView.as_view()),
]
