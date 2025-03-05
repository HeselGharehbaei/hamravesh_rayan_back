from django.urls import path
from .views import *

urlpatterns= [
    path('new/', DispatcherProfileCreateView.as_view()),
    path('', DispatcherProfileListView.as_view()),
    path('edit/', DispatcherProfileEditView.as_view()),
    path('add-shaba/', DispatcherShabaAdd.as_view()),
]