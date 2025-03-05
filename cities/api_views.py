from rest_framework import generics
from core.utils.mixins import ApiKeyValidationMixin
from .models import State, City
from .api_serializers import StateSerializer, CitySerializer


class StateListView(ApiKeyValidationMixin, generics.ListAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer

    def initial(self, request, *args, **kwargs):
        # Validate API key
        self.check_api_key(request)
        # Proceed with the usual `initial` method
        super().initial(request, *args, **kwargs)


class CityListView(ApiKeyValidationMixin, generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def initial(self, request, *args, **kwargs):
        # Validate API key
        self.check_api_key(request)
        # Proceed with the usual `initial` method
        super().initial(request, *args, **kwargs)

