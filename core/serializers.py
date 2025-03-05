from rest_framework import serializers
from .models import HeadTags

class HeadTagsSerializer(serializers.ModelSerializer):
    page_urls = serializers.StringRelatedField(many=True)  # لیست URLها را به‌صورت استرینگ نمایش می‌دهد

    class Meta:
        model = HeadTags
        fields = ['page_urls', 'head_tag']  # فقط این دو فیلد را باز می‌گرداند
