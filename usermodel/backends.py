# backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, phone=None, password=None, **kwargs):
        UserModel = get_user_model()

        # Authenticate based on either email or phone
        if email:
            user = UserModel.objects.filter(email=email).first()
        elif phone:
            user = UserModel.objects.filter(phone=phone).first()
        else:
            return None

        # Check if the user exists and the provided password is correct
        if user and user.check_password(password):
            return user
        else:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        