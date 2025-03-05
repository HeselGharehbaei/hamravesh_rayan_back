from rest_framework import generics, permissions, status
from rest_framework.response import Response

from core.utils.permissions import get_user_permissions

from .serializers import BusinessSerializer
from .models import Business


class AdminBusinessListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BusinessSerializer

    def list(self, request, *args, **kwargs):
        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_business' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        queryset = Business.objects.all()
        # Serialize the queryset
        serializer = BusinessSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)