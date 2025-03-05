from rest_framework import generics, status
from rest_framework.response import Response

from core.utils.permissions import get_user_permissions
from .models import DispatcherProfile
from .serializers import DispatcherProfileAdminSerializer

class DispatcherAdminView(generics.ListAPIView):
    serializer_class = DispatcherProfileAdminSerializer
    queryset = DispatcherProfile.objects.filter(confirm=True)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Check user's permissions
        user_permissions = get_user_permissions(request.user)
        if 'view_order' not in user_permissions:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)