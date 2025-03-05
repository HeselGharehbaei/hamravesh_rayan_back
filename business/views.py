from django.shortcuts import get_object_or_404, render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from business.models import Business, BusinessType, BusinessShowCase
from business.serializers import BusinessSerializer, BusinessTypeSerializer, BusinessShowCaseSerializer
from userprofile.models import RealUserProfile, LegalUserProfile
from django.utils import timezone


class BusinessTypeListView(generics.ListAPIView):
    serializer_class = BusinessTypeSerializer
    queryset = BusinessType.objects.all()


class BusinessCreateView(generics.CreateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Business.objects.all()
    def create(self, request, *args, **kwargs):
        # Create the serializer instance with the incoming request data
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        try:
            # Validate the data and raise an exception if there are validation errors
            serializer.is_valid(raise_exception=True)
            
            # Save the validated data to create a new business instance
            self.perform_create(serializer)
            
            # Return a custom response with a 200 status code instead of 201
            return Response(
                {
                    'message': 'Business created successfully',
                    'status': 200,
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            # If validation fails, return a custom error response
            return Response(
                {
                    'message': 'Validation failed',
                    'status': 400,
                    'errors': e.detail  # Include the detailed error messages from the serializer
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class BusinessRetrieveView(generics.RetrieveAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'  # The field used to look up the object (e.g., 'id')

    def get_queryset(self):
        """
        Returns the list of objects that this view will manage.
        Although `get_queryset` is optional for `RetrieveAPIView`,
        defining it helps in controlling which objects can be accessed.
        """
        return Business.objects.all()

    def get_object(self):
        """
        Override this method to retrieve a specific business object.
        Also includes custom permission checks if needed.
        """
        business = super().get_object()
        self.check_user_permission(business, self.request.user)  # Custom permission check
        return business

    def check_user_permission(self, business, user):
        """
        Custom method to check if the user has the required permissions to access the business.
        """
        if business.real_profile:
            if business.real_profile.user != user:
                raise PermissionDenied('شما اجازه دسترسی ندارید')
        elif business.legal_profile:
            if business.legal_profile.user_admin != user:
                raise PermissionDenied('شما اجازه دسترسی ندارید')
        else:
            raise ValidationError('پروفایل کسب و کار یافت نشد')
        
class BusinessUpdateView(generics.UpdateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'  # Use the 'id' field for lookup

    def get_queryset(self):
        return Business.objects.all()

    def get_object(self):
        business = super().get_object()
        self.check_user_permission(business, self.request.user)
        return business

    def check_user_permission(self, business, user):
        """
        Check if the user has permission to access or modify the business.
        """
        if business.real_profile:
            if business.real_profile.user != user:
                raise PermissionDenied('شما اجازه تغییر ندارید')
        elif business.legal_profile:
            if business.legal_profile.user_admin != user:
                raise PermissionDenied('شما اجازه تغییر ندارید')
        else:
            raise ValidationError('برای کسب و کار پروفایل یافت نشد')

    def update(self, request, *args, **kwargs):
        """
        Override the update method to include custom validation logic.
        """
        business = self.get_object()

        # Check if the business has orders
        if business.has_orders():
            # Only allow updates to the logo field
            allowed_fields = ['logo']
            data_keys = request.data.keys()

            # If any field other than 'logo' is in the update request, raise an error
            if any(field not in allowed_fields for field in data_keys):
                raise ValidationError('This business has orders and only the logo can be updated.')

        # Proceed with the update if conditions are met
        return super().update(request, *args, **kwargs)


# Separate view to handle deleting a business object
class BusinessDestroyView(generics.DestroyAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'  # Use the 'id' field for lookup

    def get_queryset(self):
        return Business.objects.all()

    def get_object(self):
        business = super().get_object()
        self.check_user_permission(business, self.request.user)
        return business

    def check_user_permission(self, business, user):
        """
        Check if the user has permission to access or delete the business.
        """
        if business.real_profile:
            if business.real_profile.user != user:
                raise PermissionDenied('شما اجازه تغییر ندارید')
        elif business.legal_profile:
            if business.legal_profile.user_admin != user:
                raise PermissionDenied('شما اجازه تغییر ندارید')
        else:
            raise ValidationError('برای کسب و کار پروفایل یافت نشد')

    def destroy(self, request, *args, **kwargs):
        """
        Override the destroy method to include custom validation logic.
        """
        business = self.get_object()
        if business.has_orders():
            raise ValidationError('This business has orders and cannot be deleted.')
        return super().destroy(request, *args, **kwargs)

#seprate end
class BusinessListView(generics.ListAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        real_profile = RealUserProfile.objects.filter(user=user).first()
        legal_profile = LegalUserProfile.objects.filter(user_admin=user).first()

        if legal_profile:
            return Business.objects.filter(legal_profile=legal_profile).all()
        elif real_profile:
            return Business.objects.filter(real_profile=real_profile).all()

        else:
            raise ValidationError('ابتدا پروفایل خود را تعریف کنید')


class BusinessShowCaseListView(generics.ListAPIView):
    serializer_class= BusinessShowCaseSerializer
    def get_queryset(self):
        now = timezone.localtime()

        return  BusinessShowCase.objects.filter(expire_date__gte=now,)
    
