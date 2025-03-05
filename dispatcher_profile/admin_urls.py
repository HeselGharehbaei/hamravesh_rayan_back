from django.urls import path

from .admin_views import DispatcherAdminView

urlpatterns =[
    path('', DispatcherAdminView.as_view()),
]