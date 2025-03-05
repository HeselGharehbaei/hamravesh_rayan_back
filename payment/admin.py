from django.contrib import admin
from .models import *

admin.site.register(CreditCo)
admin.site.register(Credit)
class WalletAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    list_display = ('user', 'amount', 'created_at', 'updated_at')
admin.site.register(Wallet, WalletAdmin)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'authority', 'tracking_code', 'payment_status', 'date')

admin.site.register(PaymentAmount, PaymentAdmin)
admin.site.register(IncreaseWalletCo)
admin.site.register(GiveWalletCharge)