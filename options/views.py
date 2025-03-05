from django.http import Http404
import jdatetime
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.decorators import APIView
from rest_framework.response import Response
from collections import defaultdict

from business.models import Business
from userprofile.models import LegalUserProfile, RealUserProfile
from .models import *
from .serializers import *


class PackagesListView(generics.ListAPIView):
    queryset = Package.objects.all().order_by('-created_at')
    serializer_class = PackageSerializers


class SizesListView(generics.ListAPIView):
    serializer_class = SizeSerializers
    def get_queryset(self):
        package_id = self.kwargs['pack_id']
        return Size.objects.filter(package_size__id=package_id).order_by('-created_at')


class OrderingsListView(generics.ListAPIView):
    queryset = OrderingOption.objects.all()
    serializer_class = OrderingOptionsSerializers


class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializers


class BusinessServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializers
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Service.objects.filter(business__real_profile__user=user, is_private=True)
  

class ServicesListView(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        user = request.user

        # Public services: Only services that are not private and have no business
        public_services = Service.objects.filter(business__isnull=True, is_private=False)

        # Business-specific services: Only for users who are business owners
        if user.is_authenticated:
            business_services = Service.objects.filter(business__real_profile__user=user, is_private=True)
        else:
            business_services = Service.objects.none()  # If not logged in, return an empty list

        # Preparing the response data
        response_data = {
            'public_services': ServiceSerializers(public_services, many=True).data,
            'business_services': ServiceSerializers(business_services, many=True).data
        }

        return Response(response_data)


class ContentListView(generics.ListAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializers


class ValueCheck(APIView):
    def get(self, request, *args, **kwargs):
        value = kwargs['value']

        all_values = Value.objects.all().order_by('-created_at')

        if not all_values.exists():
            raise Http404("ارزشی برای اعتبارسنجی تعریف نشده است")
        max_value = 0
        for val in all_values:
            if max_value < val.max_value:
                max_value = val.max_value

        if value > max_value:
            return Response({'message': 'ارزش کالای شما از حد مجاز بیشتر است.'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        else:
            return Response({'message': 'مورد قبول است'}, status=status.HTTP_202_ACCEPTED)


class ContentValueListView(generics.ListAPIView):
    serializer_class = ContentValueSerializers

    def get(self, request, *args, **kwargs):
        # Retrieve data from the database as lists
        content_data = Content.objects.all().order_by('-created_at')
        value_data = Value.objects.all().order_by('created_at')


        # Use ContentSerializers and ValueSerializers to serialize the data
        content_serializer = ContentSerializers(content_data, many=True)
        value_serializer = ValueSerializers(value_data, many=True)
        # Construct the data to be passed to ContentValueSerializers
        data_to_serialize = {
            'Content_data': content_serializer.data,
            'Value_data': value_serializer.data
        }
        # Use ContentValueSerializers to serialize the combined data
        ser_data = ContentValueSerializers(data=data_to_serialize)
        # Check if the serialization is valid
        if ser_data.is_valid():
            # Return the serialized data
            return Response(ser_data.initial_data)
        else:
            # Return an error response
            return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailableServiceDaysAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Get 'service_title' from the request body
        service_title = request.data.get('service_title')

        # Ensure 'service_title' is provided
        if not service_title:
            return Response({"error": "service_title is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the days without service
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
            service = Service.objects.filter(title=service_title).first()
            if not service:
                return Response({"message": "سرویس یافت نشد"}, status=status.HTTP_400_BAD_REQUEST)
            request_time = datetime.datetime.now()
            if request_time.time() >= service.hour:
                finish_today_order_date = jdatetime.date.fromgregorian(date=today_gregorian)
                today_to_ten_days_range.remove(finish_today_order_date)
                if request.user.is_authenticated:
                    userp = request.user
                    legal = LegalUserProfile.objects.filter(user_admin=userp).first()
                    real = RealUserProfile.objects.filter(user=userp).first()
                    business = None
                    if legal:
                        business = Business.objects.filter(legal_profile=legal)
                    elif real:
                        business = Business.objects.filter(real_profile=real)
                    
                    if business:
                        bus_ids = [str(bus.id) for bus in business]
                        if ('C3YS' in bus_ids and service.id == '10L9' and request_time.time() <= datetime.time(9, 15, 0)):
                            today_to_ten_days_range.append(finish_today_order_date)
                        elif ('C3YS' in bus_ids and service.id == 'C7HI' and request_time.time() <= datetime.time(14, 30, 0)):
                            today_to_ten_days_range.append(finish_today_order_date)

                    
                
            #remove thursday if servicebe for afternoon
            # if service_title=='سرویس درون شهری - عصرگاهی':
            #     today_to_ten_days_range = [
            #         day for day in today_to_ten_days_range if day.weekday() != 5  # Remove Thursdays (3 = Thursday)
            #     ]
            #remove all days for specialservice
            if service_title=='سرویس اختصاصی (با ما تماس بگیرید)':
                today_to_ten_days_range = [
                    
                ]
            # Calculate available service days
            available_service_days = list(set(today_to_ten_days_range) - set(no_service_days_list))

            # Organize available service days by month
            available_service_days_by_month = defaultdict(list)
            for available_service_day in available_service_days:
                available_service_days_by_month[available_service_day.month - 1].append(available_service_day.day)

            # Convert defaultdict to a regular dictionary
            available_service_days_by_month = dict(available_service_days_by_month)

            # Ensure all months are included in the dictionary, even if they are empty
            for month in range(12):
                if month not in available_service_days_by_month:
                    available_service_days_by_month[month] = []
                    
            return Response(available_service_days_by_month)

        except Exception as e:
            # Return a 500 error if something goes wrong
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)