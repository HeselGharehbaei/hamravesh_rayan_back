from django.apps import AppConfig
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class BusinessConfig(AppConfig):
    name = 'business'
    verbose_name = _('Business')


