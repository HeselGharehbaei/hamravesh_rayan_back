from rest_framework import generics

from .models import BlogModel
from .serializers import BlogSerializers

class BlogViews(generics.ListAPIView):
    serializer_class = BlogSerializers
    queryset = BlogModel.objects.all()