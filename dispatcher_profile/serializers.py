from rest_framework import serializers
from .models import DispatcherProfile

class DispatcherProfileAdminSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = DispatcherProfile
        fields = ['id', 'first_name', 'last_name', 'full_name']  # فقط فیلدهای مدل

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name and obj.last_name else ""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name'] = self.get_full_name(instance)  # اینجا دستی اضافه می‌کنی
        return data

class DispatcherProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)
    user = serializers.CharField(required=False)

    class Meta:
        model = DispatcherProfile
        exclude = ['service', 'zone', 'business']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('service', None)

        # Check if a profile already exists for this user
        if DispatcherProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError({'user': "کاربر قبلا پروفایل ثبت کرده"})

        # Check if a profile with the same national code exists
        if 'national_code' in validated_data:
            national_code = validated_data['national_code']
            if DispatcherProfile.objects.filter(national_code=national_code).exists():
                raise serializers.ValidationError({'national_code': "سفیر با این کد ملی قبلا ثبت شده است"})

        # Create the profile if no validation errors
        instance = DispatcherProfile.objects.create(user=user, **validated_data)
        return instance

    def update(self, instance, validated_data):
    # Check if the instance is already confirmed in the database
        if instance.confirm:
            raise serializers.ValidationError({'message': 'پروفایل از قبل تایید شده '})
        
        # Proceed with the update if not confirmed
        return super().update(instance, validated_data)