from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from payment.models import Credit, Wallet
from payment.serializers import CreditSerializer, WalletSerializers


class CreditCreateView(generics.CreateAPIView):
    serializer_class = CreditSerializer
    permission_classes = [IsAuthenticated]
    queryset = Credit.objects.all()


class CreditListView(generics.ListAPIView):
    serializer_class = CreditSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Credit.objects.filter(user=self.request.user)



class WalletCreateView(generics.CreateAPIView):
    serializer_class = WalletSerializers
    permission_classes = [IsAuthenticated]
    queryset = Wallet.objects.all()


class WalletListView(generics.ListAPIView):
    serializer_class = WalletSerializers
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
