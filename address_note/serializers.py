from rest_framework import serializers

from address_note.models import AddressNote
from cities.serializers import DistrictSerializer, CitySerializer, StateSerializer

class AddressNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressNote
        fields = '__all__'


class AddressNoteListSerializer(serializers.ModelSerializer):
    # district = DistrictSerializer(required=False, allow_null=True)
    city = CitySerializer(required=False, allow_null=True)
    state = StateSerializer(required=False, allow_null=True)
    class Meta:
        model = AddressNote
        fields = '__all__'


