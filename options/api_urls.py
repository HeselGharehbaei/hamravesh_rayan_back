from django.urls import path
from .api_views import *


urlpatterns = [
    path('service/', ServiceListView.as_view()),
    path('size/', SizesListView.as_view()),
    path('contents/', ContentListView.as_view()),
    path('available_service_days/', AvailableServiceDaysAPIView.as_view())
]
