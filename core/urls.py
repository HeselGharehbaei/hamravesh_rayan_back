from django.urls import path
from .views import RobotsTxtView
from .views import HeadTagsListView


urlpatterns = [
    path("robots.txt", RobotsTxtView.as_view(content_type="text/plain"), name="robots"),
    path('headtags/', HeadTagsListView.as_view(), name='headtags-list'),
]