from django.urls import path

from .admin_views import AdminBusinessListView

urlpatterns = [
    path('', AdminBusinessListView.as_view()),
]