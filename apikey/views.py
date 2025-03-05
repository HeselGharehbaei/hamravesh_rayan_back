import secrets
from django.shortcuts import render

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound


from .models import ApiKeyModel
from .serializers import ApiKeySerializers

class CreateApiKeyView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApiKeySerializers
    queryset = ApiKeyModel.objects.all()


class ListApiKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApiKeySerializers
    def get(self, request, *args, **kwargs):
        bus_id = self.kwargs['bus_id']  # Correct way to access kwargs
        api_keys = ApiKeyModel.objects.filter(business_id=bus_id)
        # Serialize the queryset and return the response
        serializer = self.serializer_class(api_keys, many=True)
        return Response(serializer.data)

class UpdateApiKeyView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApiKeySerializers
    def get_object(self):
        bus_id = self.kwargs.get('bus_id')
        try:
            return ApiKeyModel.objects.get(business_id=bus_id)
        except ApiKeyModel.DoesNotExist:
            raise NotFound(f"No API key found for business_id {bus_id}.")


class RotateApiKey(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        # Check if the user is authorized to rotate API keys (e.g., admin)
        if not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        api_key_id = request.data.get('id')
        if not api_key_id:
            return Response({"message": "enter id"})
        try:
            api_key = ApiKeyModel.objects.get(id=api_key_id)
        except ApiKeyModel.DoesNotExist:
            return Response({"detail": "API key not found."}, status=status.HTTP_404_NOT_FOUND)

        api_key.key = secrets.token_hex(32)  # Generate a new key
        api_key.save()

        return Response({"api_key": api_key.key, "expiration_date": api_key.expiration_date}, status=status.HTTP_200_OK)