from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .models import Dispatcher
from usermodel.models import CustomUser

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return None
        try: 
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if not token:
                    raise AuthenticationFailed('No authorization token provided')
                validated_token = UntypedToken(token)
                user_id = validated_token.get('user_id')
                user = CustomUser.objects.filter(id=user_id).first()
                if user:
                    return (user, None)

            else:
                token = auth_header
                if not token:
                    raise AuthenticationFailed('No authorization token provided')
                validated_token = UntypedToken(token)
                user_id = validated_token.get('user_id')
                user = Dispatcher.objects.filter(id=user_id).first()
                if user:
                    return (user, None)
            
            raise AuthenticationFailed('User not found')
        
        except TokenError as e:
            raise AuthenticationFailed(f'Token error: {e}')
        except InvalidToken as e:
            raise AuthenticationFailed(f'Invalid token: {e}')

        return None
