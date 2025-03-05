from django.urls import path
from .views import *

urlpatterns = [
    path('real/new/', RealUserProfileCreate.as_view()),
    path('real/', RealUserProfileListView.as_view()),
    path('real/edit/', RealUserProfileEdit.as_view()),
    path('legal/new/', LegalUserProfileCreate.as_view()),
    path('legal/', LegalUserProfileListView.as_view()),
    path('legal/detail/<str:id>/', LegalUserProfileDetailView.as_view()),
    path('legal/edit/<str:id>/', LegalUserProfileUpdateView.as_view()),
    path('agent/', AgentCompanyListCreateView.as_view()),
    path('agent/<str:id>/', AgentCompanyRetrieveUpdateDestroyView.as_view()),
]