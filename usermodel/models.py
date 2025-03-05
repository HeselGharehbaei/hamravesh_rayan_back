import re
from jsonschema.exceptions import ValidationError

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, AbstractUser
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from core.models import BaseModel,TimeStampMixin, MyFourDigitModel


phone_pattern_iran = r'^09\d{9}$'
class CustomUserManager(BaseUserManager):
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

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Create and return a superuser with a username (email or phone) and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(username, password, **extra_fields)

class CustomUser(MyFourDigitModel, TimeStampMixin, AbstractBaseUser, PermissionsMixin):
    """
    Custom user model extending AbstractBaseUser.
    """
    # Add your custom fields here
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        # validators=[
        #     validate_email_or_phone
        # ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('Email'), unique=True, blank=True, null=True)
    phone = models.CharField(_('Phone'), max_length=20, unique=True, null=True, blank=True)
    phone_auth = models.BooleanField(_('Phone Auth'), default=False)
    password = models.CharField(verbose_name=_('password'), max_length=200, null=True, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_(
                                        'Designates whether this user should be treated as active. '
                                        'Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    def __str__(self):
        return f'{self.username}'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class CustomResetPassword(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, verbose_name=_('user'), on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=10, verbose_name=('code'), null=True, blank=True)
    check_code = models.BooleanField(_('check code'), default=False, null=True, blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('reset password code')
        verbose_name_plural = _('reset password codes')

class CustomRegisterLoginCode(BaseModel, TimeStampMixin, models.Model):
    username = models.CharField(_('username'), max_length=100)
    code = models.CharField(_('code'), max_length=4, null=True, blank=True)
    check_code = models.BooleanField(_('check code'), default=False, null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('register code')
        verbose_name_plural = _('register codes')
