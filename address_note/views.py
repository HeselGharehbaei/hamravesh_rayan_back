from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import AddressNote
from .serializers import AddressNoteSerializer, AddressNoteListSerializer


class AddressNoteCreateView(generics.CreateAPIView):
    serializer_class = AddressNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        ser_data = self.get_serializer(data=request.data)
        ser_data.is_valid(raise_exception=True)
        address_note = AddressNote.objects.create(user=user, **ser_data.validated_data)
        return Response({'message': 'با موفقیت افزوده شد'}, status=status.HTTP_201_CREATED)


class AddressNoteListView(generics.ListAPIView):
    serializer_class = AddressNoteListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user)


class AddressNoteSenderListView(generics.ListAPIView):
    serializer_class = AddressNoteListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user, sender=True)


class AddressNoteReceiverListView(generics.ListAPIView):
    serializer_class = AddressNoteListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user, sender=False)


class AddressNoteDetailView(generics.ListAPIView):
    serializer_class = AddressNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user, id=self.kwargs['id'])

class AddressUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = AddressNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user, id=self.kwargs['id'])


class AddressDeleteView(generics.DestroyAPIView):
    serializer_class = AddressNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    def get_queryset(self):
        user = self.request.user
        return AddressNote.objects.filter(user=user, id=self.kwargs['id'])


class AddressSearchView(generics.ListAPIView):
    serializer_class = AddressNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        title = self.request.query_params.get('title')
        return AddressNote.objects.filter(user=self.request.user, title__icontains=title)
