from django.db import models
from django.utils.translation import gettext as _

from core.models import BaseModel,TimeStampMixin

from usermodel.models import CustomUser


class CreditCo(BaseModel, TimeStampMixin, models.Model):
    coefficient = models.FloatField(_('coefficient'), default=0.1)

    def __str__(self):
        return f'{self.coefficient}'

    class Meta:
        verbose_name = _('credit coefficient')
        verbose_name_plural = _('credit coefficients')


class Credit(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, verbose_name=_('user'), on_delete=models.CASCADE)
    amount = models.FloatField(_('amount'), default=0.0)

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        verbose_name = _('credit')
        verbose_name_plural = _('credits')


class Wallet(BaseModel, TimeStampMixin, models.Model):
    user = models.OneToOneField(CustomUser, verbose_name=_('user'), on_delete=models.CASCADE)
    amount = models.FloatField(_('amount'), default=0.0)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')


class PaymentAmount(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(CustomUser, verbose_name=_('user'), on_delete=models.CASCADE)
    amount = models.FloatField(_('amount'), default=0.0)
    tracking_code = models.TextField(_('tracking code'))
    authority = models.CharField(_('authority'), max_length=50)
    payment_status = models.CharField(_('payment amount'), max_length=50, default=False)
    date = models.DateTimeField(_('date and time'), auto_now_add=True)
    deposit = models.BooleanField(_('deposit'), default=True)
    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        verbose_name = _('payment amount')
        verbose_name_plural = _('payment amounts')


class IncreaseWalletCo(BaseModel, TimeStampMixin, models.Model):
    Coefficient = models.FloatField(_('Coefficient'),default=.05)

    def __str__(self):
        return f'{self.Coefficient}'

    class Meta:
        verbose_name = _('wallet increase amount')
        verbose_name_plural = _('wallet increase amounts')

class GiveWalletCharge(BaseModel, TimeStampMixin, models.Model):
    start_date = models.CharField(max_length=10,verbose_name='start_date', null=True, blank=True)
    finish_date = models.CharField(max_length=10,verbose_name='finish_date', null=True, blank=True)
    amount = models.IntegerField(verbose_name='amount', null=True, blank=True)
    def __str__(self) -> str:
        return f'{self.amount}'