from django.http import JsonResponse
from jose import JWTError
from rest_framework.permissions import BasePermission
# from rest_framework.request import Request
import jwt
from django.conf import settings
from rest_framework import status
from config.settings import API_KEY
from .models import Dispatcher

# class IsDispatcher(BasePermission):
#     def has_permission(self, request):
#         """
#         Check if the dispatcher is authenticated based on the JWT token provided in the request header.
#         """
#         token = request.headers.get('Authorization', '').split(' ')[-1]
#         if not token:
#             return False
#         try:
#             # Decode and verify the token
#             decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

#             # Access user information from the decoded payload
#             # username
#             user_id = decoded_payload['user_id']
#             user = Dispatcher.objects.filter(id=user_id)
#             if user.exists():
#                 return True
#             else:
#                 return False
#         except jwt.ExpiredSignatureError:
#         # Handle token expiration
#             return False
#         except JWTError:
#             # Handle other JWT errors
#             return False

# myapp/permissions.py

# import jwt
# from rest_framework import permissions
# # from django.conf import settings
# # from myapp.models import Dispatcher
# from rest_framework.exceptions import AuthenticationFailed

# class IsAuthenticatedWithToken(permissions.BasePermission):
#     """
#     Custom permission to check if the user is authenticated with a valid JWT token.
#     """

#     def has_permission(self, request, view):
#         token = request.headers.get('Authorization', '').split(' ')[-1]
#         if not token:
#             raise AuthenticationFailed('There isn\'t any authorization token')

#         try:
#             # Decode and verify the token
#             decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
#             # Access user information from the decoded payload
#             user_id = decoded_payload['user_id']
#             user = Dispatcher.objects.filter(id=user_id).first()
            
#             if user:
#                 request.user = user
#                 return True
#             else:
#                 raise AuthenticationFailed('User not found')

#         except jwt.ExpiredSignatureError:
#             # Handle token expiration
#             raise AuthenticationFailed('Token has expired')
#         except jwt.InvalidTokenError:
#             # Handle other JWT errors
#             raise AuthenticationFailed('Invalid token')

#         return False

from rest_framework import permissions
from .authentication import CustomJWTAuthentication

class IsAuthenticatedWithToken(permissions.BasePermission):
    """
    Custom permission to check if the user is authenticated with a valid JWT token.
    """

    def has_permission(self, request, view):
        auth_result = CustomJWTAuthentication().authenticate(request)
        if auth_result is not None:
            user, _ = auth_result
            request.user = user
            return True
        return False