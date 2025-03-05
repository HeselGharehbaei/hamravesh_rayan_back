import jdatetime
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from core.utils.mixins import ApiKeyValidationMixin
from .models import *
from .admin_serializers import *
from core.utils.permissions import get_user_permissions


class ServiceAdminListView(ApiKeyValidationMixin, generics.ListAPIView):
    serializer_class = ServiceAdminSerializers
    queryset = Service.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ContentAdminListView(ApiKeyValidationMixin, generics.ListAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentAdminSerializers

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)