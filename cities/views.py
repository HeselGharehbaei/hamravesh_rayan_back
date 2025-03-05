from django.shortcuts import render
from rest_framework import generics
from .models import State, City, District
from .serializers import StateSerializer, CitySerializer, DistrictSerializer


class StateListView(generics.ListAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer


class CityListView(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer


class DistrictListView(generics.ListAPIView):
    serializer_class = DistrictSerializer
    
    def get_queryset(self):
        city_id = self.request.GET.get('id')  # Correctly access query parameters
        if city_id:
            return District.objects.filter(cities__id=city_id)  # Adjust filter to match model relationship
        return District.objects.all()

# from pymongo import MongoClient

# # Example connection setup
# client = MongoClient('mongodb://localhost:27017/')
# db = client.get_database('rayan')

# # Correct way to check if db is not None
# if db is not None:
#     print("//////////////Database connection successful.")
# else:
#     print("***************Failed to connect to the database.")
