from django.urls import path
from .views import *

urlpatterns = [
    path('new/', BusinessCreateView.as_view()),
    path('type/', BusinessTypeListView.as_view()),
    path('<str:id>/', BusinessRetrieveView.as_view()),
    path('edit/<str:id>/', BusinessUpdateView.as_view()),
    path('delete/<str:id>/', BusinessDestroyView.as_view()),
    path('', BusinessListView.as_view()),
    path('show/case/', BusinessShowCaseListView.as_view()),
]
