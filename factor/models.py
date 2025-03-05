from django.db import models
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin


class FactorCounter(BaseModel, TimeStampMixin, models.Model):
    tracking_code = models.CharField(max_length=15, verbose_name=_('tracking_code'))
    count = models.IntegerField(_('count'))

    def __str__(self) -> str:
        return self.tracking_code