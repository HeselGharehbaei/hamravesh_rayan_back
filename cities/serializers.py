from rest_framework import serializers
from .models import State, City, District


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    district = DistrictSerializer(many=True)
    class Meta:
        model = City
        fields = ('id', 'name', 'district', 'created_at', 'updated_at')

class StateSerializer(serializers.ModelSerializer):
    city = CitySerializer(many=True)
    class Meta:
        model = State
        fields = ('id', 'name', 'city', 'created_at', 'updated_at')



