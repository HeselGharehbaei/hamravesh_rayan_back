import datetime

from jalali_date import datetime2jalali

from rest_framework import serializers

from options.models import CheckServiceCount, Service, Size, Value, Content, Package
from options.serializers import ServiceSerializers, SizeSerializers, ValueSerializers, ContentSerializers, PackageSerializers
from cities.serializers import DistrictSerializer, CitySerializer, StateSerializer
from .models import Order


class AdminAllOrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializers()
    pursuit = serializers.SerializerMethodField()
    user_business = serializers.StringRelatedField()
    dispatcher_sender = serializers.StringRelatedField()
    dispatcher_reciever = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ['pursuit', 'user_business', 'pickup_date', 'order_number', 'receiver_name', 'receiver_phone', 'receiver_zone', 'tracking_code', 'service','dispatcher_sender', 'dispatcher_reciever', 'created_at', 'updated_at']

    def get_pursuit(self, obj):
        return obj.get_pursuit_display_translated() if obj.pursuit else None
    
    def to_representation(self, instance):
        # Customize the representation of the serialized data here
        representation = super().to_representation(instance)
        # Add or modify fields in the 'representation' dictionary as needed
        original_datetime_str_c = representation['created_at']
        original_datetime_str_u = representation['updated_at']
        original_datetime_c = datetime.datetime.strptime(original_datetime_str_c, "%Y/%m/%d %H:%M:%S")
        original_datetime_u = datetime.datetime.strptime(original_datetime_str_u, "%Y/%m/%d %H:%M:%S")
        formatted_datetime_c = datetime2jalali(original_datetime_c)
        formatted_datetime_u = datetime2jalali(original_datetime_u)
        changed_format_datetime_c = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
        changed_format_datetime_u = formatted_datetime_u.strftime("%Y/%m/%d %H:%M:%S")
        representation['created_at'] = changed_format_datetime_c 
        representation['updated_at'] = changed_format_datetime_u

        # representation['is_grouped_by_tracking_code'] = True

        return representation


class AdminOrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializers()
    size = SizeSerializers()
    content = ContentSerializers()
    package = PackageSerializers()
    sender_city = CitySerializer()
    receiver_city = CitySerializer()
    sender_state = StateSerializer()
    receiver_state = StateSerializer()

    pursuit = serializers.SerializerMethodField()
    user_business = serializers.StringRelatedField()
    dispatcher_sender = serializers.StringRelatedField()
    dispatcher_reciever = serializers.StringRelatedField()
    
    small_count = serializers.IntegerField(required=False, default=0)
    medium_count = serializers.IntegerField(required=False, default=0)
    big_count = serializers.IntegerField(required=False, default=0)


    class Meta:
        model = Order
        fields = '__all__'

    def get_pursuit(self, obj):
        return obj.get_pursuit_display_translated() if obj.pursuit else None

    def to_representation(self, instance):
        # Customize the representation of the serialized data here
        representation = super().to_representation(instance)
        # Add or modify fields in the 'representation' dictionary as needed
        original_datetime_str_c = representation['created_at']
        original_datetime_str_u = representation['updated_at']
        original_datetime_c = datetime.datetime.strptime(original_datetime_str_c, "%Y/%m/%d %H:%M:%S")
        original_datetime_u = datetime.datetime.strptime(original_datetime_str_u, "%Y/%m/%d %H:%M:%S")
        formatted_datetime_c = datetime2jalali(original_datetime_c)
        formatted_datetime_u = datetime2jalali(original_datetime_u)
        changed_format_datetime_c = formatted_datetime_c.strftime("%Y/%m/%d %H:%M:%S")
        changed_format_datetime_u = formatted_datetime_u.strftime("%Y/%m/%d %H:%M:%S")
        representation['created_at'] = changed_format_datetime_c 
        representation['updated_at'] = changed_format_datetime_u

        # representation['is_grouped_by_tracking_code'] = True

        return representation