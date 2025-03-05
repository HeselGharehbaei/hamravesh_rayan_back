from django.db import models
from django_resized import ResizedImageField
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel
from userprofile.models import RealUserProfile, LegalUserProfile
# from django_jalali.db import models as jmodels


class BusinessType(BaseModel, TimeStampMixin, models.Model):
    title = models.CharField(verbose_name=_('title'),max_length=50)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Business Type')
        verbose_name_plural = _("Business Types")


class Business(MyFourDigitModel, TimeStampMixin, models.Model):
    logo = ResizedImageField(_('logo'), size=[250, 250], force_format='PNG', upload_to='logos', null=True, blank=True)
    real_profile = models.ForeignKey(RealUserProfile, verbose_name=_('real profile'), on_delete=models.CASCADE, null=True, blank=True)
    legal_profile = models.ForeignKey(LegalUserProfile, verbose_name=_('legal profile'), on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(verbose_name=_('name'), max_length=30)
    b_type = models.ForeignKey(BusinessType, verbose_name=_('business type'), on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=10, verbose_name=_('postal_code'), null=True, blank=True)
    economic_number = models.CharField(max_length=12, verbose_name=_('economic_number'), null=True, blank=True)
    registration_number = models.CharField(max_length=7, verbose_name=_('registration_number'), null=True, blank=True)
    national_code = models.CharField(verbose_name=_('national code'), max_length=11, null=True, blank=True)
    address = models.TextField(_('address'), null=True, blank=True)
    phone = models.CharField(_('phone'), max_length=11, null=True, blank=True)
    bill = models.BooleanField(verbose_name=_('bill'), default=False)

    def __str__(self):
        return self.name
    

    def has_orders(self):
    # Checks if the business has any orders
        return self.orders_user.exists()


    class Meta:
        verbose_name = _('Business')
        verbose_name_plural = _('Businesses')


class BusinessShowCase(BaseModel, TimeStampMixin):
    image = models.ImageField(_('image'), upload_to='business_showcase', null=True, blank=True)
    title = models.CharField(verbose_name=_('name'), max_length=400, null=True, blank=True)
    link = models.URLField(verbose_name=_('link'), null=True, blank=True)
    expire_date= models.DateTimeField(verbose_name=_('expire_date'), null=True, blank=True)
    

    def __str__(self):
        return self.title


    class Meta:
        verbose_name = _('BusinessShowCase')
        verbose_name_plural = _('BusinessShowCases')

