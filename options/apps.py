from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OptionsConfig(AppConfig):
    name = 'options'
    verbose_name = _('Options')
