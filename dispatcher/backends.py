from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Dispatcher

class DispatcherBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Dispatcher.objects.get(username=username)
            if user.check_password(password):
                return user
        except Dispatcher.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Dispatcher.objects.get(pk=user_id)
        except Dispatcher.DoesNotExist:
            return None