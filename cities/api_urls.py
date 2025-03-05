from django.urls import path
from .api_views import StateListView, CityListView

urlpatterns = [
    path('state_cities/', StateListView.as_view()),
]