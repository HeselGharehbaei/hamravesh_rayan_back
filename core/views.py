from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import generics
from .models import HeadTags
from .serializers import HeadTagsSerializer
# Create your views here.


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"


class HeadTagsListView(generics.ListAPIView):
    queryset = HeadTags.objects.all()
    serializer_class = HeadTagsSerializer    

#print(" test for action")