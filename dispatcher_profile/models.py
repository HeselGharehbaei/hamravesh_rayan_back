from django.db import models
from django.utils.translation import gettext as _
from django_resized import ResizedImageField
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError



from business.models import Business
from core.utils.validations import validate_national_code, validate_phone_number
from core.models import BaseModel, TimeStampMixin

from cities.models import City
from dispatcher.models import Dispatcher
from options.models import Service


class Zone_disp(BaseModel, TimeStampMixin, models.Model):
    zone_id = models.CharField(max_length=10, unique=True, verbose_name=_('Zone ID'))

    def __str__(self):
        return self.zone_id
    class Meta:
        verbose_name = _('dispatcher zone')
        verbose_name_plural = _('dispatcher zones')

class DispatcherProfile(BaseModel, TimeStampMixin, models.Model):
    guaranty_types=(
        ('check','چک'),
        ('safte', 'سفته'),
        ('sayer', 'سایر')
    )
    genders=(
        ('man', 'مرد'),
        ('woman', 'زن')
    )

    # zone_choises =(
    #     ('1', '۱'),
    #     ('2', '۲'),
    #     ('3', '۳'),
    #     ('4', '۴'),
    #     ('5', '۵'),
    #     ('6', '۶')
    # )

    education_choises=(
        ('diploma', 'دیپلم'),
        ('advanced diploma', 'فوق دیپلم'),
        ('bachelor', 'لیسانس'),
        ('master', 'فوق لیسانس'),
        ('doctorate', 'دکترا'),
        ('post-doctorate', 'فوق دکترا')
    )
    user = models.OneToOneField(Dispatcher, verbose_name=_('user'), on_delete=models.CASCADE, related_name='profile', unique=True, error_messages={'unique':"قبلا پروفایل خود را ثبت کرده‌اید"}, null=True, blank=True)
    image = ResizedImageField(verbose_name=_('image'), size=[250, 250], quality=85, force_format='JPEG', upload_to='dispatcher/profile', null=True, blank=True)
    city = models.CharField(_('city'), max_length=50, null=True, blank=True)
    address = models.CharField(_('address'), max_length=400, null=True, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=10, validators=[MinLengthValidator(10)], null=True, blank=True)#required=false
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)#required=false
    first_name = models.CharField(_('first name'), max_length=30, null=True, blank=True)
    last_name = models.CharField(_('last name'), max_length=30,null=True, blank=True)
    gender = models.CharField(_('gender'),max_length=10, default='man', choices=genders,null=True, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=11, validators=[validate_phone_number], null=True, blank=True)
    role = models.CharField(_('role'), max_length=50, default=_('dispatcher'), null=True, blank=True)
    education = models.CharField(_('education'), max_length=50, choices=education_choises, null=True, blank=True)
    shaba_number = models.CharField(_('shaba number'), max_length=26, validators=[MinLengthValidator(26)], null=True, blank=True)
    # identity_documents = models.FileField(_('identity documents'), upload_to='dispatcher/identity', null=True, blank=True)

    birth_certificate_no = models.CharField(_('birth certificate number'), max_length=11, null=True, blank=True)
    national_code = models.CharField(_('national code'), validators=[validate_national_code],max_length=11, unique=True, null=True, blank=True)
    national_cart1 = ResizedImageField(_('national cart1'),  size=[800, 600], quality=85, force_format='JPEG',upload_to='dispatcher/national_cart1', null=True, blank=True)
    national_cart2 = ResizedImageField(_('national cart2'), size=[800, 600], quality=85, force_format='JPEG', upload_to='dispatcher/national_cart2', null=True, blank=True)
    # contract = models.FileField(_('contract'), upload_to='dispatcher/contract', null=True, blank=True)
    # clearances = models.FileField(_('clearances'), upload_to='dispatcher/contract', null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)

    certificate_no = models.CharField(_('certificate no'), max_length=10, validators=[MinLengthValidator(10)], null=True, blank=True)
    certificate_image = ResizedImageField(_('certificate image'), size=[800, 600], quality=85, force_format='JPEG', upload_to='dispatcher/certificate', null=True, blank=True)
    expiration_certificate_date = models.DateField(_('expiration certificate date'), null=True, blank=True)

    guaranty_type = models.CharField(_('guaranty type'), max_length=100, choices=guaranty_types, null=True, blank=True)
    guaranty_amount = models.IntegerField(_('guaranty amount'), null=True, blank=True)
    guarantor_first_name = models.CharField(_('guarantor first name'), max_length=30, null=True, blank=True)
    guarantor_last_name = models.CharField(_('guarantor last name'), max_length=30, null=True, blank=True)
    guarantor_phone_number = models.CharField(_('guarantor phone number'), max_length=11, validators=[validate_phone_number], null=True, blank=True)
    guarantor_national_code = models.CharField(_('guarantor national code'), validators=[validate_national_code],max_length=10, null=True, blank=True)

    business = models.ManyToManyField(Business, verbose_name=_('business'), null=True, blank=True)
    zone = models.ManyToManyField(Zone_disp,verbose_name=_('zone'), null=True, blank=True)
    service = models.ManyToManyField(Service, verbose_name=_('service'), null=True, blank=True)
    confirm = models.BooleanField(_('confirm'), default=False, null=True, blank=True)
    
    # def clean(self):
    #     # Call the parent class clean method
    #     super().clean()

    #     # Check if the national_code is the same as the guarantor_national_code
    #     if self.national_code and self.guarantor_national_code:
    #         if self.national_code == self.guarantor_national_code:
    #             raise ValidationError({
    #                 'guarantor_national_code': _("کد ملی ضامن نباید با کد ملی شما یکی باشد.")
                # })
    def __str__(self):
        return self.last_name

    class Meta:
        verbose_name = _('dispatcher profile')
        verbose_name_plural = _('dispatcher profiles')