from django.urls import path
from .views import StateListView, CityListView, DistrictListView

urlpatterns = [
    path('', CityListView.as_view()),
    path('state/', StateListView.as_view()),
    path('district/', DistrictListView.as_view())
]