from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError


from dispatcher.permission import IsAuthenticatedWithToken
from dispatcher_payment.views import ZarinpalAPI
from .serializers import *


class DispatcherProfileCreateView(generics.CreateAPIView):
    serializer_class = DispatcherProfileSerializer
    permission_classes = [IsAuthenticatedWithToken]


class DispatcherProfileListView(generics.ListAPIView):
    serializer_class = DispatcherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DispatcherProfile.objects.filter(user=self.request.user)


class DispatcherProfileEditView(generics.RetrieveUpdateAPIView):
    serializer_class = DispatcherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DispatcherProfile.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        return obj

    def update(self, request, *args, **kwargs):
        try:
            # Call the update method and handle validation exceptions
            return super().update(request, *args, **kwargs)
        except ValidationError as exc:
            # Extract the first field and message if validation errors exist
            if isinstance(exc.detail, dict):
                # Extract the first field and its error message
                field, messages = next(iter(exc.detail.items()))
                if isinstance(messages, list) and messages:
                    # Use the first message in the list
                    message = messages[0]
                else:
                    message = messages  # Handle case when messages is a single string
            else:
                # Fallback for non-dictionary error detail
                message = exc.detail
                field = 'error'  # Use a default field name if none is provided
            message = f'[{message}]'
            # Return the formatted message as a dictionary
            return Response({field: message}, status=status.HTTP_400_BAD_REQUEST)


class DispatcherShabaAdd(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DispatcherProfile.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        prof_disp = queryset.first()
        shaba = request.data.get('shaba')
        if not shaba:
            return Response({'message': 'شماره شبا مورد نیازاست'}, status=status.HTTP_400_BAD_REQUEST)
        zarinpal_api = ZarinpalAPI()

        # Call the add_cart method to add the IBAN
        message, status_code, data = zarinpal_api.add_cart(shaba)

        if status_code == 200:
            prof_disp.shaba_number = shaba
            prof_disp.save()
            # Return success response with the data
            return Response({'message': 'با موفقیت افزوده شد'}, status=status.HTTP_202_ACCEPTED)
        else:
            # Return error response if the mutation fails
            # return Response({"error": message, "details": data}, status=status_code)
            return Response({'message':'مشکلی درافزودن شماره شبا بوجود آمده است'}, status=status_code)
