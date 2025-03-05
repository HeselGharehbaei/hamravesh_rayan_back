from rest_framework import serializers
from django.utils.translation import gettext as _ 
from business.models import Business, BusinessType, BusinessShowCase
from userprofile.models import RealUserProfile, LegalUserProfile


class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = '__all__'    


class BusinessSerializer(serializers.ModelSerializer):
    has_orders = serializers.SerializerMethodField()


    class Meta:
        model = Business
        fields = '__all__'

    def get_has_orders(self, obj):
        # Returns whether the business has any orders
        return obj.has_orders()
    
    
    def create(self, validated_data):
        if validated_data['bill']:
            required_fields = ['national_code', 'postal_code', 'economic_number', 'registration_number', 'address', 'phone']
            for field in required_fields:
                if field not in self.initial_data:
                    raise serializers.ValidationError(f' {_(field)} ضروری است')
        bus_name = validated_data['name']        
        user = self.context['request'].user
        if LegalUserProfile.objects.filter(user_admin=user).exists():
            validated_data['legal_profile'] = LegalUserProfile.objects.get(user_admin=user)
            if Business.objects.filter(legal_profile=validated_data['legal_profile'], name=bus_name).exists():
                raise serializers.ValidationError('نام کسب و کار تکراری است')
        elif RealUserProfile.objects.filter(user=user).exists():
            validated_data['real_profile'] = RealUserProfile.objects.get(user=user)
            if Business.objects.filter(real_profile=validated_data['real_profile'], name=bus_name).exists():
                raise serializers.ValidationError(({
                    'message': 'نام کسب و کار تکراری است'
                }))
        else:
            raise serializers.ValidationError(({
                    'message': 'نام کسب و کار تکراری است'
                }))
        

        return Business.objects.create(**validated_data)


class BusinessShowCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessShowCase
        fields = '__all__'   