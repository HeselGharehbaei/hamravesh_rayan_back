from datetime import timedelta
from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField
from jdatetime import datetime as jalali_datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from django_q.tasks import schedule
from django.utils import timezone
from datetime import timedelta

from django.core.validators import MinValueValidator, MaxValueValidator
from core.utils.validations import validate_date_within_10_days_and_jalali_date_format, validate_phone_number
from core.models import BaseModel,TimeStampMixin, MyFourDigitModel

from business.models import Business
from usermodel.models import CustomUser
from options.models import *
from cities.models import *
from dispatcher_profile.models import DispatcherProfile




class Order(MyFourDigitModel, TimeStampMixin, models.Model):
    pursuit_choises = (
        ('waiting for payment', 'در انتظار پرداخت'),
        ('waiting for collection', 'در انتظار جمع آوری'),
        ('canceled', 'لغو شده'),
        ('revoke', 'ابطال شده'),
        ('collected', 'جمع آوری شده'),
        ('waiting for distribution', 'مرکز پردازش'),
        ('get by ambassador', 'دریافت توسط رای‌پیک'),
        ('delivered', 'تحویل شده'),
        ('returned', 'مرجوع شده'),
    )

    pre_order = models.IntegerField(default=0, verbose_name=_('pre order'))
    user_business = models.ForeignKey(Business, verbose_name=_('user_business'), on_delete=models.PROTECT, related_name='orders_user')

    order_number = models.IntegerField(_('order number'), validators=[MinValueValidator(1000), MaxValueValidator(9999)], null=True, blank=True)
    order_description = models.TextField(_('order description'),null=True, blank=True)
    address_description = models.TextField(_('address description'),null=True, blank=True)
    package = models.ForeignKey(Package, verbose_name=_('package'), on_delete=models.SET_NULL, related_name='orders_packages', null=True, blank=True)
    size = models.ForeignKey(Size, verbose_name=_('size'), on_delete=models.SET_NULL, related_name='orders_sizes', null=True, blank=True)
    count = models.IntegerField(_('count'), default=0)
    content = models.ForeignKey(Content, verbose_name=_('content'), on_delete=models.SET_NULL, related_name='orders_content', null=True, blank=True)
    service = models.ForeignKey(Service,  verbose_name=_('service'), on_delete=models.SET_NULL, related_name='orders_service', null=True, blank=True)
    # value = models.ForeignKey(Value, verbose_name=_('value'), on_delete=models.SET_NULL, related_name='orders_value', null=True, blank=True)
    value = models.PositiveIntegerField(verbose_name=_('value'), null=True, blank=True)
    pickup_date = models.CharField(_('pickup_date'), max_length=10, validators=[validate_date_within_10_days_and_jalali_date_format])

    sender_title = models.CharField(_('sender_title'), max_length=50, null=True, blank=True)
    sender_address = models.CharField(_('sender_address'), max_length=200)
    sender_plaque = models.CharField(_('sender_plaque'), max_length=20, null=True, blank=True)
    sender_stage = models.CharField(_('sender_stage'), max_length=10, null=True, blank=True)
    sender_state = models.ForeignKey(State, verbose_name=_('sender_state'), on_delete=models.SET_NULL, related_name='sender_state', null=True, blank=True)
    sender_city = models.ForeignKey(City, verbose_name=_('sender_city'), on_delete=models.SET_NULL, related_name='sender_city', null=True, blank=True)
    sender_district = models.CharField(_('sender_district'), max_length=30, null=True, blank=True)
    sender_unity = models.CharField(_('sender_unity'), max_length=15, null=True, blank=True)
    sender_name = models.CharField(_('sender_name'), max_length=100, null=True, blank=True)
    sender_phone = models.CharField(_('sender_phone'), validators=[validate_phone_number], max_length=11, null=True, blank=True)
    sender_map_link = models.URLField(_('sender_map_link'), null=True, blank=True)
    sender_lat = models.CharField(_('sender_lat'), max_length=20, null=True, blank=True)
    sender_long = models.CharField(_('sender_long'), max_length=20, null=True, blank=True)
    sender_zone = models.CharField(_('sender_zone'),max_length=10, null=True, blank=True)

    receiver_title = models.CharField(_('receiver_title'), max_length=50, null=True, blank=True)
    receiver_address = models.CharField(_('receiver_address'), max_length=200)
    receiver_plaque = models.CharField(_('receiver_plaque'), max_length=20, null=True, blank=True)
    receiver_stage = models.CharField(_('receiver_stage'), max_length=10, null=True, blank=True)
    receiver_unity = models.CharField(_('receiver_unity'), max_length=15, null=True, blank=True)
    receiver_state = models.ForeignKey(State, verbose_name=_('receiver_state'), on_delete=models.SET_NULL, related_name='receiver_state', null=True, blank=True)
    receiver_city = models.ForeignKey(City, verbose_name=_('receiver_city'), on_delete=models.SET_NULL, related_name='receiver_city', null=True, blank=True)
    receiver_district = models.CharField(_('receiver_district'), max_length=30, null=True, blank=True)
    receiver_name = models.CharField(_('receiver_name'), max_length=100, null=True, blank=True)
    receiver_phone = models.CharField(_('receiver_phone'), validators=[validate_phone_number], max_length=11, null=True, blank=True)
    receiver_map_link = models.URLField(_('receiver_map_link'), null=True, blank=True)
    receiver_lat = models.CharField(_('receiver_lat'), max_length=20, null=True, blank=True)
    receiver_long = models.CharField(_('receiver_long'), max_length=20, null=True, blank=True)
    receiver_zone = models.CharField(_('receiver_zone'),max_length=10, null=True, blank=True)

    price = models.PositiveIntegerField(_('price'), default=0)
    total_price = models.PositiveIntegerField(_('total_price'), default=0, null=True, blank=True)
    pursuit = models.CharField(_('pursuit'), max_length=100, choices=pursuit_choises, null=True, blank=True)
    bank_code = models.CharField(_('bank code'), max_length=50, null=True, blank=True)
    tracking_code = models.CharField(_('tracking_code'), max_length=13, default=0)
    delivery_code = models.CharField(_('delivery_code'), max_length=5, default=0)
    is_multi = models.BooleanField(_('is_multi'), default=True, null=True, blank=True)

    payment_status = models.BooleanField(_('payment_status'), default=False)
    payment = models.CharField(_('payment'), max_length=100, null=True, blank=True)
    credit = models.BooleanField(_('credit'), default=False)

    dispatcher_sender = models.ForeignKey(DispatcherProfile, verbose_name=_('dispatcher_sender'), on_delete=models.SET_NULL, limit_choices_to={'confirm': True}, related_name='dispatcher_sender',null=True, blank=True)
    dispatcher_reciever = models.ForeignKey(DispatcherProfile, verbose_name=_('dispatcher_reciever'), on_delete=models.SET_NULL, limit_choices_to={'confirm': True}, related_name='dispatcher_reciever', null=True, blank=True)


    def __str__(self):
        return f'{self.tracking_code}'
    
    def get_pursuit_display_translated(self):
        return dict(self.pursuit_choises).get(self.pursuit, _('Unknown'))
    
    def clean(self):
        required_fields = ['size', 'content', 'service', 'value', 'sender_city', 'receiver_city']
        
        # Check that all required fields are not null during creation
        for field in required_fields:
            if not getattr(self, field) and not self.pk:
                raise ValidationError(_(f'{field.replace("_", " ").capitalize()} cannot be null when creating an order.'))
        
    def save(self, *args, **kwargs):
        # Apply the validator to format the date
        try:
            self.full_clean()  # This will run the validators automatically
        except ValidationError as e:
            # Handle the validation error if necessary
            raise e        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')

# @receiver(post_save, sender=Order)
# def schedule_status_change(sender, instance, created, **kwargs):
#     if created:
#         # Schedule the task to run 60 minutes after the order is created
#         schedule(
#             'order.tasks.change_order_status',  # The function path to execute
#             instance.id,  # Argument to pass to the function (order ID)
#             next_run=timezone.now() + timedelta(minutes=60),  # Schedule to run in 60 minutes
#             repeats=1  # Ensure the task only runs once
#         )


class QRCode(BaseModel, TimeStampMixin, models.Model):
    image = ResizedImageField( size=[250, 250],quality=100,force_format='PNG',upload_to='qrcodes/')

    def __str__(self):
        return f'{self.image.url}'


class OrderStatusLogs(BaseModel, TimeStampMixin, models.Model):
    order = models.ForeignKey(Order, verbose_name=_('order'), on_delete=models.CASCADE, related_name='orderslog', null=True, blank=True)
    get_by_ambassador = models.DateTimeField(verbose_name='get_by_ambassador', null=True, blank=True)
    delivered = models.DateTimeField(verbose_name='delivered', null=True, blank=True)
    returned = models.DateTimeField(verbose_name='returned', null=True, blank=True)
    service_time_difference_get = models.DurationField(verbose_name='service_time_difference_get', null=True, blank=True)
    service_time_difference_deliver = models.DurationField(verbose_name='service_time_difference_deliver', null=True, blank=True)
    get_intime = models.BooleanField(verbose_name='get_intime', null=True, blank=True)
    deliver_intime = models.BooleanField(verbose_name='deliver_intime', null=True, blank=True)

    def __str__(self):
        return f'hi'


class ProcessExcel(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exceluser', null=True, blank=True)
    count = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username}'