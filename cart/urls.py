from django.urls import path

from .views import *

urlpatterns =[
    path('new/', CartCreateView.as_view()),
    path('', CartListView.as_view()),
    path('edit/<str:id>/', CartUpdateView.as_view()),
    path('delete/', CartDeleteView.as_view())
]