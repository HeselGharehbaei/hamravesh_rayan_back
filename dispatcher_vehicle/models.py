from django.db import models
from django.utils.translation import gettext as _
from django_resized import ResizedImageField
from django.core.validators import MinLengthValidator


from core.models import BaseModel, TimeStampMixin
from dispatcher.models import Dispatcher

class DispatcherVehicle(BaseModel, TimeStampMixin, models.Model):
    vehicle_choises = (
        ('motorcycle','موتورسیکلت'),
        ('truck','وانت'),
        ('van', 'ون')
    )
    dispatcher = models.ForeignKey(Dispatcher, verbose_name=_('dispatcher'), on_delete=models.CASCADE, null=True, blank=True)
    motorcycle_type = models.CharField(_('motorcycle type'),max_length=30, null=True, blank=True)
    vehicle_documents = ResizedImageField(_('vehicle documents'), size=[800, 600], quality=85, force_format='JPEG', upload_to='dispatcher/vehicle', null=True, blank=True)
    vehicle = models.CharField(_('vehicle'), max_length=12, default='motorcycle', choices=vehicle_choises, null=True, blank=True)    
    new_plaque = models.BooleanField(_('new plaque'), default=True, null=True, blank=True)
    plaque = models.CharField(_('plaque'), max_length=8, validators=[MinLengthValidator(8)], null=True, blank=True)
    plaque_image = ResizedImageField(_('plaque image'), size=[800, 600], quality=85, force_format='JPEG', upload_to='dispatcher/plaque', null=True, blank=True)
    #insurance = models.BooleanField(_('insurance'), default=False)
    insurance_no = models.CharField(_('insurance no'), max_length=11, validators=[MinLengthValidator(11)], null=True, blank=True)
    insurance_image = ResizedImageField(_('insurance image'), size=[800, 600], quality=85, force_format='JPEG', upload_to='dispatcher/insurance', null=True, blank=True)
    expiration_insurance_date = models.DateField(_('expiration insurance date'), null=True, blank=True)
    confirm = models.BooleanField(_('confirm'), default=False, null=True, blank=True)

    def __str__(self):
        return f'{self.plaque}-{self.dispatcher}'
    

    def get_vehicle_display_translated(self):
        return dict(self.vehicle_choises).get(self.vehicle, _('Unknown'))
    
    class Meta:
        verbose_name = _('dispatcher_vehicle')
        verbose_name_plural = _('dispatcher_vehicles')