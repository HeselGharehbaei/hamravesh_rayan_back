from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CityConfig(AppConfig):
    name = 'cities'
    verbose_name = _('Cities')
