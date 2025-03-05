from django.db import models
from django.utils.translation import gettext as _
# from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel
from cities.models import State, City, District
from usermodel.models import CustomUser

class AddressNote(MyFourDigitModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=50, null=True, blank=True)
    sender = models.BooleanField(default=False, verbose_name=_("sender"))
    address = models.TextField(_('address'))
    plaque = models.CharField(_('plaque'), max_length=20, null=True, blank=True)
    stage = models.PositiveSmallIntegerField(_('stage'), null=True, blank=True)
    state = models.ForeignKey(State, verbose_name=_('state'), on_delete=models.CASCADE,
                              null=True, blank=True)
    city = models.ForeignKey(City, verbose_name=_('city'), on_delete=models.CASCADE,
                             null=True, blank=True)
    zone = models.CharField(_('zone'), max_length=10)
    district = models.CharField(_('district'), max_length=30)
    unity = models.CharField(_('unity'), max_length=20, null=True, blank=True)
    name = models.CharField(_('name'), max_length=50)
    phone = models.CharField(_('phone'), max_length=11)
    map_link = models.URLField(_('map link'), null=True, blank=True)
    lat = models.CharField(_('lat'), max_length=20, null=True, blank=True)
    long = models.CharField(_('long'), max_length=20, null=True, blank=True)
    def __str__(self):
        return f'{self.name} - {self.address}'

    class Meta:
        verbose_name = _('address note')
        verbose_name_plural = _('address notes')
