from rest_framework import serializers
from .models import DispatcherVehicle

class DispatcherVehicleSerializer(serializers.ModelSerializer):
    dispatcher = serializers.CharField(required=False)

    class Meta:
        model = DispatcherVehicle
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        if 'plaque' in validated_data:
            vehicle = DispatcherVehicle.objects.filter(plaque = validated_data['plaque'])
            if vehicle:
                raise serializers.ValidationError({'message': 'این پلاک قبلا ثبت شده است'})
        
        instance = DispatcherVehicle.objects.create(dispatcher=user, **validated_data)
        # if instance.insurance == True:
        #     if instance.insurance_no or not instance.insurance_image:
        #         raise serializers.ValidationError({'message':'اطلاعات مربوط به بیمه نامه وارد نشده'})

        return instance
    
    def update(self, instance, validated_data):
        if 'plaque' in validated_data and validated_data['plaque'] != instance.plaque:
            vehicle_exists = DispatcherVehicle.objects.filter(plaque=validated_data['plaque']).exists()
            if vehicle_exists:
                raise serializers.ValidationError({'message': 'این پلاک قبلا ثبت شده است'})
        # Check if the instance is already confirmed in the database
        if instance.confirm:
            raise serializers.ValidationError({'message': 'وسیله نقلیه از قبل تایید شده '})
        
        # Proceed with the update if not confirmed
        return super().update(instance, validated_data)

