from rest_framework import serializers
from .models import *


class ServiceSerializers(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()  # فیلد سفارشی اضافه می‌کنیم

    class Meta:
        model = Service
        fields = ('id', 'title', 'description')  # فیلدهای موجود به‌علاوه فیلد سفارشی

    def get_description(self, obj):
        # ساختن متن ترکیبی برای فیلد description
        return f"جمع آوری: {obj.pickup_time}, تحویل: {obj.delivery_time}"


class SizeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('id', 'title', 'description') 


class ContentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ('id', 'title')


