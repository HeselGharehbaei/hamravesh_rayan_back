from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsermodelConfig(AppConfig):
    name = 'usermodel'
    verbose_name = _('Usermodel')
