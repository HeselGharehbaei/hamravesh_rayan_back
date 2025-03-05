from django.urls import path

from .admin_views import *

urlpatterns = [
    path('', AdminOrdersView.as_view()),
    path('details/<str:tracking_code>/', AdminOrderDetailsView.as_view()),
    path('edit/<str:tracking_code>/', AdminOrderEditView.as_view()),
    path('delete/<str:tracking_code>/', AdminOrderDeleteView.as_view()),
    path('editable-fields/', EditableFieldsView.as_view()),
    path('noneditable-fields/', NonEditableFieldsView.as_view()),

]