from rest_framework import serializers
from .models import *


class ServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class SizeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class PackageSerializers(serializers.ModelSerializer):
    size = SizeSerializers(many=True)
    class Meta:
        model = Package
        fields = ['id', 'title', 'short_description', 'description', 'icon', 'size']

class OrderingOptionsSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrderingOption
        fields = '__all__'


class ValueSerializers(serializers.ModelSerializer):
    class Meta:
        model = Value
        fields = '__all__'


class ContentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = '__all__'


class ContentValueSerializers(serializers.Serializer):
    Content_data = ContentSerializers(many=True)
    Value_data = ValueSerializers(many=True)
