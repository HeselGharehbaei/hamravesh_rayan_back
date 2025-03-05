from  django.urls import path

from .views import BlogViews

urlpatterns = [
    path('', BlogViews.as_view())
]