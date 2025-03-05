from django.urls import path
from .views import *

urlpatterns = [
    path('new/<str:id>/', OrderCreateView.as_view()),
    path('edit/<str:tracking_code>/', OrderUpdateView.as_view()),
    path('edit/all/<str:bus_id>/', OrderUpdateAllView.as_view()),
    path('decrease/multi/<str:bus_id>/', OrderDecreaseMulti.as_view()),
    path('delete/<str:bus_id>/<str:tracking_code>/', OrderDeleteOneView.as_view()),
    path('delete/<str:bus_id>/', OrderDeleteView.as_view()),
    path('delete-single/<str:bus_id>/', OrderDeleteSingleView.as_view()),
    path('group/<str:bus_id>/', OrderListGroupView.as_view()),
    path('', OrderListView.as_view()),
    path('cancel/', CancelOrderView.as_view()),
    path('waiting/cancel/', CancelWaitingOrderView.as_view()),
    path('details/<str:bus_id>/', OrderListDetailsView.as_view()),
    path('notpaied/<str:bus_id>/', OrderListNotPaiedView.as_view()),
    path('notpaied/size/<str:bus_id>/', OrderListSizeNotPaiedView.as_view()),
    path('payment/<str:code>/<str:bus_id>/', OrderListDetailsPaymentView.as_view()),
    path('pursuit/', PursuitOrder.as_view()),
    path('inway/', OrderInwayListView.as_view()),
    path('chart/', OrderChartCount.as_view()),
    path('count-all/', CountOrdersView.as_view()),
    path('count-inway/', CountInwayOrdersView.as_view()),
    path('paied/<str:bus_id>/', OrderPaiedListView.as_view()),
    path('pre/new/<str:bus_id>/', PreOrderCreate.as_view()),
    path('pre/delete/<str:bus_id>/', PreOrderDeleteView.as_view()),
    path('pre/<str:bus_id>/', PreOrderListView.as_view()),
    path('number/trcode/<int:order_num>/', OrderNumberTrCode.as_view()),
    path('qrinfo/', QrcodeInfoView.as_view()),
    path('multi/qrinfo/', MultiQrcodeInfoView.as_view()),
    path('waiting/qrinfo/', MultiWaitingQrcodeInfoView.as_view()),
    #filter
    path('filter/status/', OrderStatusListView.as_view()),
    path('excel/', ExcelUploadView.as_view()),
    #process bar
    path('process/bar/', ProcessBarExcel.as_view()),
]
