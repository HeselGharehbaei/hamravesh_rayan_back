import re
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request
from django.db import models
from django.utils.translation import gettext as _
from django.db import models

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel
from core.utils.validations import validate_phone_number

class DispatcherManager(BaseUserManager):
    """
    Custom manager for CustomUser.
    """
    def create_user(self, username, password=None, **extra_fields):
        """
        Create and return a regular user with a username (email or phone) and password.
        """
        if not username:
            raise ValueError(_('The Username field must be set'))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Dispatcher(MyFourDigitModel, TimeStampMixin, AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), validators=[validate_phone_number], max_length=150, unique=True)
    password = models.CharField(_("password"), max_length=128, null=True, blank=True)
    phone = models.CharField(_('Phone'), max_length=20, unique=True, null=True, blank=True)
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), blank=True, help_text=_('The groups this user belongs to.'), related_name='dispatcher_groups')
    user_permissions = models.ManyToManyField(Permission, verbose_name=_('user permissions'), blank=True, help_text=_('Specific permissions for this user.'), related_name='dispatcher_user_permissions')
    is_staff = models.BooleanField(_('staff status'), default=False, help_text=_('Designates whether the dispatcher can access the admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_('Designates whether this dispatcher account is active.'))

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']

    objects = DispatcherManager()

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('dispatcher')
        verbose_name_plural = _('dispatchers')


phone_pattern_iran = r'^09\d{9}$'


class DispatcherEnterCode(BaseModel, TimeStampMixin, models.Model):
    username = models.CharField(_('username'), validators=[validate_phone_number], max_length=50)
    code = models.CharField(_('code'), max_length=4, null=True, blank=True)
    check_code = models.BooleanField(_('check code'), default=False, null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('register code')
        verbose_name_plural = _('register codes')
        