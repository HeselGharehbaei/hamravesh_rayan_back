import datetime
from rest_framework.response import Response
from jalali_date import date2jalali
from order.models import Order
from dispatcher_profile.models import DispatcherProfile
from cities.tests import district_list

def allocation(tracking_code):
    orders = Order.objects.filter(tracking_code=tracking_code).all()
    count = 0
    for order in orders:
        count += order.count
        district = order.sender_district.name
        pickup_date = order.pickup_date
    
    #find out this district belongs to which zone
    key = None
    for k, v in district_list.items():
        if v == district:
            key = k
            print(key)
            break

    if key:
        zone = key
    else:
        # return ({'message': f"The value {district} is not found in the dictionary."})
        return(v)
    
    dispatchers_in_this_zone = DispatcherProfile.objects.filter(zone=zone)
    # count_of_dispatcher = dispatchers_in_this_zone.count()

    # today = datetime.date.today()
    # today_jalali = date2jalali(today)
    # today_jalali = str(today_jalali).replace('-', '/')

    dispatcher_order_counts = {}

    # Count orders for each dispatcher by pickup_date
    for dispatcher in dispatchers_in_this_zone:
        order_count = dispatcher.dispatcher_sender.filter(
            pickup_date=pickup_date
        ).values('tracking_code').distinct().count()
        dispatcher_order_counts[dispatcher.id] = order_count

    return(dispatcher_order_counts)


# allocation(123)  
# print('123')