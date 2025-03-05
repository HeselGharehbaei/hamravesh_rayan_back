from rest_framework import serializers, status

from business.models import Business

from .models import ApiKeyModel

class ApiKeySerializers(serializers.ModelSerializer):
    class Meta:
        model = ApiKeyModel
        fields = '__all__'

    def to_representation(self, instance):
        # Access the request method from the context
        request = self.context.get('request')
        representation = super().to_representation(instance)

        # If the request method is GET, only include specific fields
        if request and request.method == 'GET':
            return {
                'apikey': representation.get('key'),
                'expirationdate': representation.get('expiration_date'),
            }
        return representation
    
    def create(self, validated_data):
        bus_id = validated_data['business']
        bus_id = bus_id.id
        try:
            business = Business.objects.filter(id=bus_id).first()
            name = business.name
            
            instance = ApiKeyModel.objects.create(
                business_id=bus_id,
                name=name,
                **validated_data
            )
        except Exception as e:
            raise serializers.ValidationError({'message': str(e),
                                               'status': status.HTTP_400_BAD_REQUEST})

        return instance
    
    

