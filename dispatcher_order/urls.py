from django.urls import path
from .views import *

urlpatterns=[
    path('sender/', DispSenderOrderListView.as_view()),
    path('receiver/', DispReceiverOrderListView.as_view()),
    path('all/', DispAllOrderListView.as_view()),
    path('cancel/', RevokeOrderView.as_view()),
    path('collected/', CollectOrderView.as_view()),
    path('businesses-collected-orders/', DispBussinessCollectedOrders.as_view()),
    path('businesses-waiting-for-collection-orders/', DispBussinessWaitingforcollectionOrders.as_view()),
    path('distribution/', DistributOrderView.as_view()),
    path('group-distribution/', GroupDistributOrderView.as_view()),
    path('group-collected/', GroupCollectedOrderView.as_view()),
    path('group-receive/', GroupRecieveOrderView.as_view()),
    path('receive/', RecieveOrderView.as_view()),
    path('deliver/', DeliverOrderView.as_view()),
    path('return/code/', ReturnOrderCodeView.as_view()),
    path('return/', ReturnOrderView.as_view()),
    path('resendcode/', ResendCodeView.as_view()),

]