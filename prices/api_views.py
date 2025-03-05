from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.utils.mixins import ApiKeyValidationMixin
from .api_serializers import PricingSerializer
from apikey.models import ApiKeyModel
class PricingAPIView(ApiKeyValidationMixin, APIView):
    """
    API View for calculating pricing based on the PricingSerializer logic.
    """
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to calculate the total price.
        """
        serializer = PricingSerializer(data=request.data)
        # Validate the input data
        if serializer.is_valid():
            try:
                # Perform the pricing calculations in the serializer's validate method
                result = serializer.validated_data
                total_price = result["total_price"]
                # Return the total price as a response
                return Response(
                    {"total_price": total_price},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                # Return any validation errors
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Return serializer validation errors
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    def initial(self, request, *args, **kwargs):
        self.check_api_key(request)
        super().initial(request, *args, **kwargs)