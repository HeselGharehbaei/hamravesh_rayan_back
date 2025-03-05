from rest_framework import serializers
from .models import Wallet

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
    
    def to_representation(self, instance):
        # Use the default representation first
        representation = super().to_representation(instance)
        
        # Modify the 'amount' field to be amount * 10
        representation['amount'] = round(representation['amount']) 

        return representation