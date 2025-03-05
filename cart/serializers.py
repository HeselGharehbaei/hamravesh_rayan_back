from rest_framework import serializers

from .models import CartModel

class CartSerializers(serializers.ModelSerializer):
    class Meta:
        model = CartModel
        exclude = ['user']