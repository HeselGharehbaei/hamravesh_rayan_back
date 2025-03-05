from django.db import models
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel

class State(MyFourDigitModel, TimeStampMixin, models.Model):
    name = models.CharField(max_length=50, verbose_name=_('name'), unique=True)
    city = models.ManyToManyField('City', verbose_name=_('city'), related_name='city', blank=True)
    # created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('created_date'))
    # update_at = models.DateTimeField(auto_now=True, verbose_name=_('update_at'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('state')
        verbose_name_plural = _('states')


class City(MyFourDigitModel, TimeStampMixin, models.Model):
    name = models.CharField(max_length=50, verbose_name=_('name'), unique=True)
    district = models.ManyToManyField('District', verbose_name=_('district'), related_name='cities', blank=True)
    # created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('created_date'))
    # update_at = models.DateTimeField(auto_now=True, verbose_name=_('update_at'))
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')


class District(MyFourDigitModel, TimeStampMixin, models.Model):
    name = models.CharField(max_length=50, verbose_name=_('name'), unique=True)
    # created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('created_date'))
    # update_at = models.DateTimeField(auto_now=True, verbose_name=_('update_at'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('district')
        verbose_name_plural = _('districts')

