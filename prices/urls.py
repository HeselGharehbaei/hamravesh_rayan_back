from django.urls import path
from .views import *

urlpatterns = [
    path('estimate/', EstimatePrice.as_view()),
    path('validate/count/', box_fit_view),
    path('business-details/', BusinessCalculatePrice.as_view(), name='BusinessCalculatePrice'),
    path('details/', CalculatePrice.as_view(), name='CalculatePrice'),
    path('total-detailss/',TotalCalculatePrice.as_view(), name='TotalCalculatePrice'),
    path('insurance/', InsurancesView.as_view()),
    path('tax/', TaxesView.as_view()),
    path('datecheck/', CheckDateView.as_view()),
    path('check/', box_fit_view)
]
