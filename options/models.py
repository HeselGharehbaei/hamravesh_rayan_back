import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel
from business.models import Business


class Size(MyFourDigitModel, TimeStampMixin, models.Model):
    title = models.CharField(_('title'), max_length=50, unique=True)
    description = models.TextField(_('description'))
    price_co = models.FloatField(_('price'), null=True, blank=True)
    image = models.ImageField(_('image'), upload_to='size/image/', null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('size')
        verbose_name_plural = _('sizes')

class Package(MyFourDigitModel, TimeStampMixin, models.Model):
    title = models.CharField(_('title'), max_length=50, unique=True)
    short_description = models.TextField(_('short description'))
    description = models.TextField(_('description'))
    size = models.ManyToManyField('Size', related_name='package_size', blank=True)
    icon = models.ImageField(_('image'), upload_to='icons')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Package')
        verbose_name_plural = _('Packages')

class OrderingOption(MyFourDigitModel, TimeStampMixin, models.Model):
    type = models.CharField(_('type'), max_length=20)

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = _('ordering option')
        verbose_name_plural = _('ordering options')


class Vehicle(MyFourDigitModel, TimeStampMixin, models.Model):
    title = models.CharField(_('title'), max_length=50, unique=True)
    count = models.PositiveIntegerField(_('count'), default=0, null=True, blank=True)
    price = models.PositiveIntegerField(_('price'))
    # created_at = models.DateTimeField(auto_now_add=True)
    # update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('vehicle')
        verbose_name_plural = _('vehicles')

class Service(MyFourDigitModel, TimeStampMixin, models.Model):
    service_types = (
        ('درون شهری', 'درون شهری'),
        ('برون شهری', 'برون شهری'),
    )
    title = models.CharField(_('title'), max_length=100)
    company = models.CharField(_('company'), max_length=100, null=True, blank=True)
    logo = models.ImageField(_('logo'), upload_to='company/logo', null=True, blank=True)
    hour = models.TimeField(_('change mood hour'), null=True, blank=True)
    pickup_time = models.CharField(_('pickup time'), max_length=60)
    delivery_time = models.CharField(_('delivery time'), max_length=100)
    price = models.PositiveIntegerField(_('price'))
    s_type = models.CharField(_('type'), max_length=50, choices=service_types)
    vehicle = models.ManyToManyField(Vehicle, related_name='service', blank=True)
    count = models.IntegerField(_('count'), default=0)
    business = models.ManyToManyField(Business, verbose_name=_('business'), null=True, blank=True)
    is_private = models.BooleanField(_('Is Private'), default=False, help_text="Check if this service is private.")


    def __str__(self):
        return f'{self.title} - {self.s_type}'

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')

class Value(MyFourDigitModel, TimeStampMixin, models.Model):
    min_value = models.PositiveIntegerField(default=0)
    max_value = models.PositiveIntegerField(default=1000000)
    coefficient = models.FloatField(default=0.1, null=True, blank=True)

    def __str__(self):
        return f'{self.min_value}-{self.max_value}'

    class Meta:
        verbose_name = _('value')
        verbose_name_plural = _('values')

class Content(MyFourDigitModel, TimeStampMixin, models.Model):
    title = models.CharField(_('title'), max_length=90)
    # created_at = models.DateTimeField(auto_now_add=True)
    # update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('content')
        verbose_name_plural = _('contents')


class CheckServiceCount(BaseModel, TimeStampMixin, models.Model):
    pickup_date = models.CharField(_('pickup_date'), max_length=10)     
    service_type= models.CharField(_('service type'), max_length=50) 
    service_title= models.CharField(_('service title'), max_length=50) 
    service_count= models.IntegerField(default=0, verbose_name=_('service count'))


    def __str__(self):
        return self.pickup_date

    class Meta:
        verbose_name = _('checkservicecount')
        verbose_name_plural = _('checkservicecounts')
        ordering = ['pickup_date']
