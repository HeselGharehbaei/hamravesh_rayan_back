from django.urls import path
from .views import *

urlpatterns = [
    path('new/', AddressNoteCreateView.as_view()),
    path('', AddressNoteListView.as_view()),
    path('senders/', AddressNoteSenderListView.as_view()),
    path('receivers/', AddressNoteReceiverListView.as_view()),
    path('<str:id>/', AddressNoteDetailView.as_view()),
    path('edit/<str:id>/', AddressUpdateView.as_view()),
    path('delete/<str:id>/', AddressDeleteView.as_view()),
    path('search/title/', AddressSearchView.as_view()),
]