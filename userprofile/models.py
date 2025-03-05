from django.db import models
from django.utils.translation import gettext as _
from django_resized import ResizedImageField

from core.utils.validations import validate_national_code
from core.models import BaseModel,TimeStampMixin

from usermodel.models import CustomUser

roles = [
    ('admin', 'مدیر'),
    ('customer', 'مشتری')
]

class RealUserProfile(BaseModel, TimeStampMixin, models.Model):
    user = models.OneToOneField(CustomUser, verbose_name=_('user'), on_delete=models.CASCADE, error_messages={'unique':"قبلا پروفایل خود را ثبت کرده‌اید"})
    image = ResizedImageField(verbose_name=_('image'), size=[250, 250], quality=85, force_format='JPEG', upload_to='profile', null=True, blank=True)
    character = models.CharField(_('character'), max_length=15, default='حقیقی')
    address = models.CharField(_('address'), max_length=400)
    postal_code = models.CharField(_('postal code'), max_length=15, null=True, blank=True)#required=false
    national_code = models.CharField(_('national code'), validators=[validate_national_code], max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)#required=false
    father_name = models.CharField(_('father name'), max_length=30, null=True, blank=True)#required=false
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    phone_number = models.CharField(_('phone number'), max_length=11)
    role = models.CharField(_('role'), max_length=50, choices=roles)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = _('real user profile')
        verbose_name_plural = _('real user profiles')

class AgentCompany(BaseModel, TimeStampMixin, models.Model):
    company_name = models.CharField(_('company name'), max_length=150, null=True, blank=True)
    first_name = models.CharField(_('first_name'), max_length=50, null=True, blank=False)
    last_name = models.CharField(_('last_name'), max_length=50, null=True, blank=False)
    phone_number = models.CharField(_('phone number'), max_length=11)

    def __str__(self):
        return self.last_name

    class Meta:
        verbose_name = _('agent company')
        verbose_name_plural = _('agent companies')

class LegalUserProfile(BaseModel, TimeStampMixin, models.Model):
    logo = ResizedImageField(verbose_name=_('logo'), size=[250, 250], force_format='PNG', upload_to='logos', null=True, blank=True)
    user_admin = models.OneToOneField(CustomUser, verbose_name=_('admin_interface user'), on_delete=models.CASCADE, related_name='admin_user')
    user = models.ManyToManyField(CustomUser, verbose_name=_('user'), blank=True, related_name='user')
    character = models.CharField(_('character'), max_length=15, default='حقوقی')
    national_company_id = models.CharField(_('national company id'), max_length=12, null=True, blank=True)
    national_company_id_check = models.BooleanField(_('national company id check'), default=False)
    company_name = models.CharField(_('company name'), max_length=30)
    agent = models.ManyToManyField(AgentCompany, verbose_name=_('agent'), related_name='agent', blank=True)
    phone = models.CharField(_('phone number'), max_length=11,null=True, blank=True)
    company_address = models.CharField(_('company address'), max_length=400)
    role = models.CharField(_('role'), max_length=50, choices=roles)

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = _('legal user profile')
        verbose_name_plural = _('legal user profiles')
