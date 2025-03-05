from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import ApiKeyModel  # Adjust the import path as per your project

class ApiKeyPermission(BasePermission):
    """
    Custom permission class for API key authentication.
    """
    def has_permission(self, request, view):
        api_key = request.headers.get('Authorization')

        # Check if API key is provided
        if not api_key or not api_key.startswith('ApiKey '):
            raise PermissionDenied('API Key is missing or invalid.')

        api_key = api_key.split(' ')[1]  # Extract the API key

        try:
            api_key_obj = ApiKeyModel.objects.get(key=api_key)
        except ApiKeyModel.DoesNotExist:
            raise PermissionDenied('Invalid API Key.')

        # If the API key is valid, set `request.user`
        request.user = api_key_obj.user

        return True
