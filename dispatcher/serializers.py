from django.db import IntegrityError
from rest_framework import serializers
from django.utils.translation import gettext as _
from dispatcher_payment.models import Wallet
from .models import *


class DispatcherEnterSerializer(serializers.Serializer):
    username = serializers.CharField()
    code = serializers.CharField(write_only=True)

    def validate(self, data):

        #validate username
        username = data.get('username')
        code= data.get('code')

        if not re.match(phone_pattern_iran, username):
            raise serializers.ValidationError({'username': _('شماره معتبر وارد کنید(حتما در ابتدای شماره صفر قرار دهید)')}, code='invalid')
        if code is None:
            raise serializers.ValidationError({'message': 'کد را وارد کنید'})
        reg_inf = DispatcherEnterCode.objects.filter(username=username, code=code).first()
        # Check if the code exists in the record and code not exists in database
        if not reg_inf:
            raise serializers.ValidationError("کد تایید اشتباه است")
        # Delete the registration code after validation
        reg_inf.delete()
        return data    
    
    def create(self, validated_data):
        username = validated_data.get('username')
        phone = username
        if not Dispatcher.objects.filter(username=username).exists():
            # Create user
            try:
                user = Dispatcher.objects.create_user(username=username, phone=phone)
            except IntegrityError:
                # Handle IntegrityError (e.g., username already exists)
                raise serializers.ValidationError("Failed to create user.")
            Wallet.objects.create(user=user, amount=0)
            return user
        else:
            user = Dispatcher.objects.filter(username=username).first()  
            return user
    

class DispatcherEnterCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatcherEnterCode
        fields = '__all__'