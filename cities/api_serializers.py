from rest_framework import serializers
from .models import State, City



class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')

class StateSerializer(serializers.ModelSerializer):
    city = CitySerializer(many=True)
    class Meta:
        model = State
        fields = ('id', 'name', 'city')



