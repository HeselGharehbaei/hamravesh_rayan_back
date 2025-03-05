from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .serializers import *


class RealUserProfileCreate(generics.CreateAPIView):
    serializer_class = RealUserProfileSerializer
    permission_classes = [IsAuthenticated]

    # def create(self, request, *args, **kwargs):
    #     try:
    #         user = self.request.user
    #         role = 'customer'
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #
    #         RealUserProfile.objects.create(user=user, **serializer.validated_data)
    #
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     except IntegrityError:
    #         return Response({'message': 'کاربر قبلا پروفایل ثبت کرده است'}, status=400)

class RealUserProfileListView(generics.ListAPIView):
    serializer_class = RealUserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RealUserProfile.objects.filter(user=self.request.user)


class RealUserProfileEdit(generics.RetrieveUpdateAPIView):
    serializer_class = RealUserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RealUserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        return obj




class LegalUserProfileCreate(generics.CreateAPIView):
    serializer_class = LegalUserProfileSerializer
    permission_classes = [IsAuthenticated]


class LegalUserProfileListView(generics.ListAPIView):
    serializer_class = LegalUserProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        if LegalUserProfile.objects.filter(user_admin=self.request.user).first():
            return LegalUserProfile.objects.filter(user_admin=self.request.user).all()
        elif LegalUserProfile.objects.filter(user=self.request.user).first():
            return LegalUserProfile.objects.filter(user=self.request.user).all()
        else:
            return []



class LegalUserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = LegalUserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    def get_queryset(self, *args, **kwargs):
        legal_admin = LegalUserProfile.objects.filter(user_admin=self.request.user, id=self.kwargs['id'])
        legal_user = LegalUserProfile.objects.filter(user=self.request.user, id=self.kwargs['id'])
        if legal_admin.first():
            return legal_admin
        elif legal_user.first():
            return legal_user
        else:
            raise serializers.ValidationError('پروفایل یافت نشد')


class LegalUserProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = LegalUserProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = LegalUserProfile.objects.all()
    lookup_field = 'id'


class AgentCompanyListCreateView(generics.ListCreateAPIView):
    serializer_class = AgentCompanySerializer
    permission_classes = [IsAuthenticated]
    queryset = AgentCompany.objects.all()

class AgentCompanyRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AgentCompanySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    queryset = AgentCompany.objects.all()

    def destroy(self, *args, **kwargs):
        user = self.request.user
        profile_id = self.kwargs['id']
        agent_user = AgentCompany.objects.filter(id=profile_id, agent__user=user).first()
        agent_admin = AgentCompany.objects.filter(id=profile_id, agent__user_admin=user).first()
        if agent_user or agent_admin:
            agent = agent_user or agent_admin
            agent.delete()
            return Response({'message': 'با موفقیت حذف شد'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'شما اجازه حذف نماینده را ندارید'})