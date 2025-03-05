from django.urls import path
from .views import *

urlpatterns = [
    path('new/', CreateApiKeyView.as_view()),
    path('list/<str:bus_id>/', ListApiKeyView.as_view()),
    path('edit/<str:bus_id>/', UpdateApiKeyView.as_view()),
    path('rotate/', RotateApiKey.as_view())
]