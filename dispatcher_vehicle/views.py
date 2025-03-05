from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from dispatcher.permission import IsAuthenticatedWithToken
from .serializers import *


class DispatcherVehicleCreateView(generics.CreateAPIView):
    serializer_class = DispatcherVehicleSerializer
    permission_classes = [IsAuthenticatedWithToken]


class DispatcherVehicleListView(generics.ListAPIView):
    serializer_class = DispatcherVehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DispatcherVehicle.objects.filter(dispatcher=self.request.user)


class DispatcherVehicleEditView(generics.RetrieveUpdateAPIView):
    serializer_class = DispatcherVehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vehicle_id = self.kwargs['id']
        return DispatcherVehicle.objects.filter(dispatcher=self.request.user, id=vehicle_id)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, dispatcher=self.request.user)
        return obj
    
    def update(self, request, *args, **kwargs):
        try:
            # Call the update method and handle validation exceptions
            return super().update(request, *args, **kwargs)
        except ValidationError as exc:
            # Check if the validation error details are a list
            if isinstance(exc.detail, list) and len(exc.detail) == 1:
                message = exc.detail[0]  # Extract the first message if it's a list with one element
            else:
                message = exc.detail  # Otherwise, keep the original detail

            # Catch validation error and format the response
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)
    

class DispatcherVehicleDeleteView(generics.DestroyAPIView):
    serializer_class = DispatcherVehicleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        vehicle_id = self.kwargs['id']
        return DispatcherVehicle.objects.filter(dispatcher=self.request.user, id=vehicle_id, confirm=False)


