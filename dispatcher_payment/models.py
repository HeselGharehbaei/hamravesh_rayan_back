from django.db import models
from django.utils.translation import gettext as _

from core.models import BaseModel, TimeStampMixin
from dispatcher.models import Dispatcher

class Wallet(BaseModel, TimeStampMixin, models.Model):
    user = models.OneToOneField(Dispatcher, verbose_name=_('user'), on_delete=models.CASCADE)
    amount = models.FloatField(_('amount'), default=0.0)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')


class IncreaseWalletCo(BaseModel, TimeStampMixin, models.Model):
    Coefficient = models.FloatField(_('Coefficient'),default=.02)

    def __str__(self):
        return f'{self.Coefficient}'

    class Meta:
        verbose_name = _('wallet increase amount')
        verbose_name_plural = _('wallet increase amounts')


class SettelmentWallet(BaseModel, TimeStampMixin, models.Model):
    user = models.ForeignKey(Dispatcher, verbose_name=_('user'), on_delete=models.CASCADE)
    amount = models.FloatField(_('amount'), default=0.0)
    settlement = models.BooleanField(_('settelment'), default=False)
    tracking_code = models.CharField(_('tracking_code'), max_length=15)
    errormessage = models.TextField(_('error_message'), null=True, blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('settelment_Wallet')
        verbose_name_plural = _('Settelment_Wallets')