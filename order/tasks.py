from django_q.tasks import async_task
from django.utils import timezone
from datetime import timedelta
from .models import Order

def change_order_status(order_id, *args, **kwargs):
    try:
        order = Order.objects.get(id=order_id)
        if order.pursuit == 'waiting for payment':  # Only change if still pending
            order_number = order.order_number
            orders = Order.objects.filter(order_number=order_number).all()
            for order in orders:
                order.pursuit = 'canceled'  # Or any other status you want
                order.save()
    except Order.DoesNotExist:
        print(f'Order with ID {order_id} does not exist.')