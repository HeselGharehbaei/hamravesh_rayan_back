from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PricesConfig(AppConfig):
    name = 'prices'
    verbose_name = _('Prices')
