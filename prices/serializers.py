from rest_framework import serializers

class EstimateSerializer(serializers.Serializer):
    from_city = serializers.CharField()
    to_city = serializers.CharField()
    def create(self, validated_data):
        return self.validated_data

class MyDataSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    pickup_time = serializers.CharField()
    earliest_pickup_date = serializers.DateField()
    delivery_time = serializers.CharField()
    # delivery_time_date = serializers.DateField()
    logo = serializers.CharField()
    amount = serializers.IntegerField()
    message = serializers.CharField()


class PriceDetailSerializer(serializers.Serializer):
    from_city = serializers.CharField()
    to_city = serializers.CharField()
    package = serializers.ListField(child=serializers.CharField())
    size = serializers.ListField(child=serializers.CharField(), required=False)
    count = serializers.ListField(child=serializers.CharField())
    is_multi = serializers.BooleanField(default=False)

    def create(self, validated_data):
        return self.validated_data


class InsuranceSerializers(serializers.Serializer):
    price = serializers.IntegerField()
    value = serializers.CharField()

class TaxesSerializers(serializers.Serializer):
    price = serializers.IntegerField()
    value = serializers.CharField()