from django.urls import path
from .views import *

urlpatterns = [
    path('new/', DispatcherVehicleCreateView.as_view()),
    path('', DispatcherVehicleListView.as_view()),
    path('edit/<str:id>/', DispatcherVehicleEditView.as_view()),
    path('delete/<str:id>/', DispatcherVehicleDeleteView.as_view())

]