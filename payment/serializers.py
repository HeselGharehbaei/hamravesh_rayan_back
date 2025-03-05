from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import serializers

from business.models import Business
from order.models import Order
from payment.models import Credit, CreditCo, Wallet
from userprofile.models import LegalUserProfile, RealUserProfile


class CreditSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False)
    amount = serializers.FloatField(required=False)
    class Meta:
        model = Credit
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            business = get_list_or_404(
                Business,
                legal_profile=legal
            )
        elif real:
            business = get_list_or_404(
                Business,
                legal_profile=legal
            )
        else:
            raise serializers.ValidationError('ابتدا پروفایل خود را تکمیل کنید')

        credit_co = get_object_or_404(
            CreditCo
        )
        tracking_code = self.context['view'].request.POST.get('tracking_code')
        if tracking_code is None:
            raise serializers.ValidationError('کد رهگیری را وارد کنید')

        orders = Order.objects.filter(user_business__in=business, tracking_code=tracking_code, credit=False)
        if not orders.exists():
            raise serializers.ValidationError('سفارش وجود ندارد یا قبلا ثبت شده')
        price = 0
        for order in orders:
            price += order.price
            order.credit = True
            order.save()
        credit = Credit.objects.filter(user=user)
        if credit.exists():
            amount = credit.order_by('-id').first().amount
            amount += price * credit_co.coefficient
            Credit.objects.update(user=user, amount=amount)
        else:
            amount = price * credit_co.coefficient
            credit = Credit.objects.create(user=user, amount=amount)
        return credit



class WalletSerializers(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        wallet = Wallet.objects.filter(user=user).first()
        if wallet.exists():
            wallet.amount += validated_data['amount']
            wallet.save()
        else:
            wallet = Wallet.objects.create(user=user, amount=validated_data['amount'])

        return wallet

    def list_view(self):
        user = self.context['request'].user
        wallet = Wallet.objects.filter(user=user).first()
        if not wallet.exists():
            wallet = Wallet.objects.create(user=user, amount=0)
            return wallet
        else:
            return wallet




