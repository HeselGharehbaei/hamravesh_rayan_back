from django.urls import path
from .views import *
from .combination import main
from .holidayslist import get_holidays

urlpatterns = [
    path('packages/', PackagesListView.as_view()),
    path('service/', ServiceListView.as_view()),
    path('business_service/', BusinessServiceListView.as_view()),    
    path('services/', ServicesListView.as_view()),    
    path('size/<str:pack_id>/', SizesListView.as_view()),
    path('orderings/', OrderingsListView.as_view()),
    path('contents/', ContentListView.as_view()),
    path('check/value/<str:value>/', ValueCheck.as_view()),
    path('content/value/', ContentValueListView.as_view()),
    path('holidays/',get_holidays),
    path('available_service_days/', AvailableServiceDaysAPIView.as_view())
]
