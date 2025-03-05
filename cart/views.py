from django.shortcuts import render

from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound


from .serializers import CartSerializers
from .models import CartModel

class CartCreateView(generics.CreateAPIView):
    serializer_class = CartSerializers
    permission_classes = [permissions.IsAuthenticated]
    queryset = CartModel.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartListView(generics.ListAPIView):
    serializer_class = CartSerializers
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CartModel.objects.filter(user=user).all()

class CartUpdateView(generics.UpdateAPIView):
    serializer_class = CartSerializers
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        edit_card = CartModel.objects.filter(id=self.kwargs['id'], user=user)
        if edit_card.exists():
            return edit_card
        else:
            raise NotFound({'message': 'یافت نشد'})

class CartDeleteView(generics.DestroyAPIView):
    serializer_class = CartSerializers
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        cards = CartModel.objects.filter(user=user).all()
        cards.delete()
        return Response({'message': 'با موفقیت حذف شد'})

