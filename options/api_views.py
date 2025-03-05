import jdatetime
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from collections import defaultdict
from apikey.models import ApiKeyModel
from business.models import Business
from core.utils.mixins import ApiKeyValidationMixin
from userprofile.models import LegalUserProfile, RealUserProfile
from .models import *
from .api_serializers import *
from django.db.models import Q


class SizesListView(ApiKeyValidationMixin, generics.ListAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializers

    def initial(self, request, *args, **kwargs):
        # Validate API key
        self.check_api_key(request)
        # Proceed with the usual `initial` method
        super().initial(request, *args, **kwargs)


class ServiceListView(ApiKeyValidationMixin, generics.ListAPIView):
    serializer_class = ServiceSerializers

    def initial(self, request, *args, **kwargs):
        # Validate API key and attach `business_id` to the request
        self.check_api_key(request)
        super().initial(request, *args, **kwargs)

    def get_queryset(self):
        """ Fetch both private (exclusive) and public services """
        business_id = self.request.business_id  # Get `business_id` from API key
        
        return Service.objects.filter(
            Q(is_private=False) |  # Public services (visible to everyone)
            Q(is_private=True, business=business_id)  # Private services specific to this business
        )


class ContentListView(ApiKeyValidationMixin, generics.ListAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializers

    def initial(self, request, *args, **kwargs):
        # Validate API key
        self.check_api_key(request)
        # Proceed with the usual `initial` method
        super().initial(request, *args, **kwargs)

class AvailableServiceDaysAPIView(ApiKeyValidationMixin, APIView):
    def post(self, request, *args, **kwargs):
        key = self.request.headers.get('apikey')
        if not key:
            return Response({'message': 'apikey ارسال نشده است'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if the API key exists in the database
            apikey = ApiKeyModel.objects.filter(key=key).first()
            if not apikey:
                return Response({'message': 'API key نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the business ID associated with the API key
            bus_id = apikey.business.id
        except Exception as e:
            # If there is an error, return a bad request with the error message
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get 'service_title' from the request body
        service_id = request.data.get('service_id')

        # Ensure 'service_title' is provided
        if not service_id:
            return Response({"error": "service_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the days without service
            service = Service.objects.filter(id=service_id).first()
            business= Business.objects.filter(id=bus_id).first()
            if not service:
                return Response({"message": "سرویس یافت نشد"}, status=status.HTTP_400_BAD_REQUEST) 
            related_businesses = list(service.business.all())  # Retrieve the list of related businesses  
            if service.is_private:
                if business not in related_businesses:
                    return Response({"message": "این سرویس برای این بیزینس نمی باشد"}, status=status.HTTP_400_BAD_REQUEST)          
            service_title = service.title if service else None
            no_service_days = CheckServiceCount.objects.filter(service_count=0, service_title=service_title)
            no_service_days_list = [
                jdatetime.datetime.strptime(str(no_service_day.pickup_date).replace('/','-'), '%Y-%m-%d').date()
                for no_service_day in no_service_days
            ]

            # Calculate the date range from today to the next 10 days
            today_gregorian = datetime.datetime.now().date()
            today_to_ten_days_range = [
                jdatetime.date.fromgregorian(date=today_gregorian + timedelta(days=i))
                for i in range(0, 10)
            ]
            #check finish hour for service           
            request_time = datetime.datetime.now()
            if request_time.time() >= service.hour:
                finish_today_order_date = jdatetime.date.fromgregorian(date=today_gregorian)
                today_to_ten_days_range.remove(finish_today_order_date)
                if (str(bus_id) == 'C3YS' and service.id == '10L9' and request_time.time() <= datetime.time(9, 15, 0)):
                    today_to_ten_days_range.append(finish_today_order_date)
                elif (str(bus_id) == 'C3YS' and service.id == 'C7HI' and request_time.time() <= datetime.time(14, 30, 0)):
                    today_to_ten_days_range.append(finish_today_order_date)


            #remove thursday if servicebe for afternoon
            # if service_title=='سرویس درون شهری - عصرگاهی':
            #     today_to_ten_days_range = [
            #         day for day in today_to_ten_days_range if day.weekday() != 5  # Remove Thursdays (3 = Thursday)
            #     ]
            #remove all days for specialservice
            if service_title=='سرویس اختصاصی (با ما تماس بگیرید)':
                today_to_ten_days_range = []
            # Calculate available service days
            available_service_days = list(set(today_to_ten_days_range) - set(no_service_days_list))

            # Organize available service days by month
            available_service_days_by_month = defaultdict(list)
            for available_service_day in available_service_days:
                available_service_days_by_month[available_service_day.month].append(available_service_day.day)

            # Convert defaultdict to a regular dictionary
            available_service_days_by_month = dict(available_service_days_by_month)

            # Ensure all months are included in the dictionary, even if they are empty
            for month in range(1,13):
                if month not in available_service_days_by_month:
                    available_service_days_by_month[month] = []
                    
            return Response(available_service_days_by_month)

        except Exception as e:
            # Return a 500 error if something goes wrong
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def initial(self, request, *args, **kwargs):
        # Validate API key
        self.check_api_key(request)
        # Proceed with the usual `initial` method
        super().initial(request, *args, **kwargs)