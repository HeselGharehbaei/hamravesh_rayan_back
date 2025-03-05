from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
import jdatetime
from django.utils.timezone import make_aware
from django.utils.timezone import localtime


from .models import Order, OrderStatusLogs

def persian_to_english_number(persian_str):
    # Define a mapping from English digits to Persian digits
    persian_to_english_map = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    # Replace each English digit with the corresponding Persian digit
    english_str = ''.join(persian_to_english_map.get(char, char) for char in persian_str)
    return english_str

@receiver(post_save, sender=Order)
def create_order_status_logs(sender, instance, created, **kwargs):
    if created:
        OrderStatusLogs.objects.create(order=instance)


@receiver(post_save, sender=Order)
def update_order_status_logs(sender, instance, **kwargs):

    status_logs, created = OrderStatusLogs.objects.get_or_create(order=instance)

    # current_time = now()

    current_time = localtime(now())

    if instance.pursuit == 'get by ambassador':
        #get pickup_date
        persian_date_str = instance.pickup_date  # This is in the format YYYY/MM/DD

        # Step 1: Convert the Persian date string to a datetime object using jdatetime
        persian_date = jdatetime.datetime.strptime(persian_date_str, "%Y/%m/%d")

        # Step 2: Convert the Persian date to a Gregorian date
        gregorian_date = persian_date.togregorian()
        #check time of service for finish
        service_time_str_end =  persian_to_english_number(instance.service.pickup_time.split("تا ساعت")[-1].strip())  # '۱۴:۰۰'
        service_time_end = datetime.strptime(service_time_str_end, "%H:%M").time()
        service_date_time_end = make_aware(datetime.combine(gregorian_date.date(), service_time_end))
        #check time of service for start
        service_time_str_start =  persian_to_english_number(instance.service.pickup_time.split("از ساعت")[-1].split("تا ساعت")[0].strip())  # '۱۴:۰۰'
        service_time_start = datetime.strptime(service_time_str_start, "%H:%M").time()
        service_date_time_start = make_aware(datetime.combine(gregorian_date.date(), service_time_start))

        status_logs.get_by_ambassador = current_time
        if current_time > service_date_time_end:
            time_differ = current_time - service_date_time_end
        elif current_time <= service_date_time_start:
            time_differ = service_date_time_start - current_time
        else:
            time_differ = None

        status_logs.service_time_difference_get = time_differ
        status_logs.get_intime = (current_time - service_date_time_end).total_seconds() <= 0 and (current_time - service_date_time_start).total_seconds() >= 0
        
        print(service_date_time_end)

    elif instance.pursuit == 'delivered':
        #get pickup_date
        persian_date_str = instance.pickup_date  # This is in the format YYYY/MM/DD

        # Step 1: Convert the Persian date string to a datetime object using jdatetime
        persian_date = jdatetime.datetime.strptime(persian_date_str, "%Y/%m/%d")

        # Step 2: Convert the Persian date to a Gregorian date
        gregorian_date = persian_date.togregorian()
        #get the time of service
        service_time_str_end =  persian_to_english_number(instance.service.delivery_time.split("تا ساعت")[-1].strip())  # '۱۴:۰۰'
        service_time_end = datetime.strptime(service_time_str_end, "%H:%M").time()
        service_date_time_end = make_aware(datetime.combine(gregorian_date.date(), service_time_end))
        service_time_str_start =  persian_to_english_number(instance.service.delivery_time.split("از ساعت")[-1].split("تا ساعت")[0].strip()) # '۱۴:۰۰'
        service_time_start = datetime.strptime(service_time_str_start, "%H:%M").time()
        service_date_time_start = make_aware(datetime.combine(gregorian_date.date(), service_time_start))

        status_logs.delivered = current_time
        if current_time > service_date_time_end:
            time_differ = current_time - service_date_time_end
        elif current_time <= service_date_time_start:
            time_differ = service_date_time_start - current_time
        else:
            time_differ = None

        status_logs.service_time_difference_deliver = time_differ
        status_logs.deliver_intime = (current_time - service_date_time_end).total_seconds() <= 0 and (current_time - service_date_time_start).total_seconds() >= 0
    elif instance.pursuit == 'returned':
        status_logs.returned = current_time

    status_logs.save()

