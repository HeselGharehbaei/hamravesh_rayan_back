from django.urls import path
from .admin_views import *


urlpatterns = [
    path('service/', ServiceAdminListView.as_view()),
    path('contents/', ContentAdminListView.as_view()),
]