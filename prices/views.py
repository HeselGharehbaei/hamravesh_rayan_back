from datetime import datetime, timedelta
import holidays
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.decorators import api_view
from django.shortcuts import get_list_or_404, get_object_or_404
from jalali_date import datetime2jalali
from cities.models import City
from .serializers import *
from options.models import *
from core.utils.constant import tax_co, site
from rest_framework.permissions import IsAuthenticated


class EstimatePrice(APIView):
    def post(self, request):
        ser_data = EstimateSerializer(data=request.data)
        if ser_data.is_valid():
            ser_data.save()
            from_city = ser_data.validated_data.get('from_city')
            to_city = ser_data.validated_data.get('to_city')
            package = 'بسته'
            size = 'کوچک'
            title = 'سرویس درون شهری - صبحگاهی'
            if City.objects.filter(name=from_city).first() is None or City.objects.filter(name=to_city).first() is None:
                return Response({'message': 'شهر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

            if from_city == to_city:
                service_type = Service.objects.filter(
                    title=title,
                    s_type='درون شهری',
                ).first()
            else:
                service_type = Service.objects.filter(
                    s_type='برون شهری',
                ).first()

            size = get_object_or_404(
                    Size,
                    title=size,
                    package_size__title=package,
                )
            size_cost = size.price_co
            if service_type is None:
                return Response({'message': 'سرویس یافت نشد'})
            else:
                service_cost = service_type.price
            
            sum_cost = size_cost * service_cost + service_cost
            #add tax(tax*sum + insurance)
            # insurance_value = Value.objects.filter(max_value=1).first()
            # if insurance_value is None:
            #     return Response({'message': 'ارزش یافت نشد'})
            # insurance = insurance_value.coefficient * insurance_value.max_value * 10**6
            insurance = 2000
            total_cost = insurance + sum_cost + tax_co*(insurance + sum_cost)
            return Response({'total_cost':total_cost})
        else:
            return Response(ser_data.errors)
        

class CalculatePrice(APIView):
    def post(self, request):
        message = ''
        ser_data = PriceDetailSerializer(data=request.data)
        if ser_data.is_valid():
            ser_data.save()
            from_city = ser_data.validated_data.get('from_city')
            to_city = ser_data.validated_data.get('to_city')
            is_multi = ser_data.validated_data.get('is_multi')
            packages = [item for item in ser_data.validated_data.get('package')]
            packages = packages[0].split(',')
            packages = [item.strip() for item in packages]
            sizes = [list(item for item in ser_data.validated_data.get('size', None)) if ser_data.validated_data.get('size', None) is not None else None]
            if sizes[0] is not None:
                sizes = sizes[0][0].split(',')
                sizes = [item.strip() for item in sizes]
            else:
                sizes = None

            counts = [item for item in ser_data.validated_data.get('count')]
            counts = [int(count) for count in counts[0].split(',')]

        else:
            return Response({'error': ser_data.errors})

        if City.objects.filter(name=from_city).first() is None or City.objects.filter(name=to_city).first() is None:
            return Response({'message': 'شهر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        if from_city == to_city:
            service_type = Service.objects.filter(
                s_type='درون شهری',
                is_private=False,
            ).all()
            if not service_type:
                service_type = get_list_or_404(
                    Service.objects.filter(
                        s_type='درون شهری',
                        is_private=False,
                    ).all())
                message = 'متاسفانه وسیله‌ی مورد نظر شما یافت نشد سایر وسایل بررسی شدند'

        else:
            service_type = Service.objects.filter(
                s_type='برون شهری',
                is_private=False,
            ).all()
            if not service_type:
                service_type = get_list_or_404(
                    Service.objects.filter(
                        s_type='برون شهری',
                        is_private=False,
                    ).all())
                message = 'متاسفانه وسیله‌ی مورد نظر شما یافت نشد سایر وسایل بررسی شدند'

        cost = 0
        if sizes is not None:
            i = 0
            for size in sizes:
                size_cost = get_object_or_404(
                    Size,
                    title=size,
                    package_size__title=packages[i],
                )

                cost += float(size_cost.price_co) * int(counts[i])
                i += 1
        size_cost = get_object_or_404(
                    Size,
                    title='کوچک',
                )
        #decrease price from 2 or more box
        base_cost_co = float(size_cost.price_co)
        if sum(counts) >=2 and not is_multi:
            decrease_co = sum(counts)-1 + base_cost_co
        else:
            decrease_co = 0
        amount_list = [{'id': obj.id,
                        'amount': (int(obj.price) * (sum(counts) + cost)) - (int(obj.price) * decrease_co * 0.3),
                        'title': obj.title,
                        'finishHour': obj.hour,
                        'delivery_time': obj.delivery_time,
                        'pickup_time': obj.pickup_time,
                        'logo': f'{site}{obj.logo.url}',
                        'message': message
                        }

                       for obj in service_type]
        
        # Separate the list into the desired order
        first_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - صبحگاهی']
        second_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - نیم روز']
        third_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - عصرگاهی']
        other_items = [item for item in amount_list if item['title'] not in ['سرویس درون شهری - عصرگاهی',
                                                                               'سرویس درون شهری - نیم روز',
                                                                               'سرویس درون شهری - صبحگاهی',
                                                                               'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)']]
        last_item = [item for item in amount_list if item['title'] == 'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)']
        # Combine them in the desired order
        ordered_amount_list = first_item + second_item + third_item + other_items + last_item
        request_time = datetime.datetime.now()
        Ir_holidays = holidays.IR(request_time.year)


        for item in ordered_amount_list:
            if request_time.time()>= item['finishHour']:
                pickup_time = request_time + timedelta(days=1)
                while pickup_time.weekday() in Ir_holidays:
                    pickup_time += timedelta(days=1)

                    if pickup_time.weekday() == 4:
                        pickup_time += timedelta(days=1)

            else:
                pickup_time = request_time
                while pickup_time.weekday() in Ir_holidays:
                    pickup_time += timedelta(days=1)

                    if pickup_time.weekday() == 4:
                        pickup_time += timedelta(days=1)

            earliest_pickup_date = datetime2jalali(pickup_time).date()
            item['earliest_pickup_date'] = earliest_pickup_date

        serialized_data = MyDataSerializer(ordered_amount_list, many=True).data

        return JsonResponse(serialized_data, safe=False)


class BusinessCalculatePrice(APIView):
    permission_classes = [IsAuthenticated]  # این خط، API را به کاربران لاگین کرده محدود می‌کند.

    def post(self, request):
        # اگر کاربر لاگین نبود، لیست خالی برمی‌گرداند
        if not request.user.is_authenticated:
            return JsonResponse([], safe=False)
        user = request.user
        message = ''
        ser_data = PriceDetailSerializer(data=request.data)
        if ser_data.is_valid():
            ser_data.save()
            from_city = ser_data.validated_data.get('from_city')
            to_city = ser_data.validated_data.get('to_city')
            is_multi = ser_data.validated_data.get('is_multi')
            packages = [item.strip() for item in ser_data.validated_data.get('package')[0].split(',')]
            sizes = [list(item for item in ser_data.validated_data.get('size', None)) if ser_data.validated_data.get('size', None) else None]

            if sizes[0] is not None:
                sizes = sizes[0][0].split(',')
                sizes = [item.strip() for item in sizes]
            else:
                sizes = None

            counts = [int(count) for count in ser_data.validated_data.get('count')[0].split(',')]

        else:
            return Response({'error': ser_data.errors}, status=status.HTTP_400_BAD_REQUEST)

        if City.objects.filter(name=from_city).first() is None or City.objects.filter(name=to_city).first() is None:
            return Response({'message': 'شهر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        if from_city == to_city:
            service_type = Service.objects.filter(s_type='درون شهری', business__real_profile__user=user, is_private=True).all()
            if not service_type:
                service_type = get_list_or_404(Service.objects.filter(s_type='درون شهری', business__real_profile__user=user, is_private=True))
                message = 'متاسفانه وسیله‌ی مورد نظر شما یافت نشد سایر وسایل بررسی شدند'
        else:
            service_type = Service.objects.filter(s_type='برون شهری',  business__real_profile__user=user, is_private=True).all()
            if not service_type:
                service_type = get_list_or_404(Service.objects.filter(s_type='برون شهری', business__real_profile__user=user, is_private=True))
                message = 'متاسفانه وسیله‌ی مورد نظر شما یافت نشد سایر وسایل بررسی شدند'

        cost = 0
        if sizes:
            for i, size in enumerate(sizes):
                size_cost = get_object_or_404(Size, title=size, package_size__title=packages[i])
                cost += float(size_cost.price_co) * int(counts[i])

        size_cost = get_object_or_404(Size, title='کوچک')
        base_cost_co = float(size_cost.price_co)

        if sum(counts) >= 2 and not is_multi:
            decrease_co = sum(counts) - 1 + base_cost_co
        else:
            decrease_co = 0

        amount_list = [
            {
                'id': obj.id,
                'amount': (int(obj.price) * (sum(counts) + cost)) - (int(obj.price) * decrease_co * 0.3),
                'title': obj.title,
                'finishHour': obj.hour,
                'delivery_time': obj.delivery_time,
                'pickup_time': obj.pickup_time,
                'logo': f'{site}{obj.logo}',
                'message': message
            }
            for obj in service_type
        ]
        seen_titles = set()
        unique_amount_list = []
        for item in amount_list:
            if item['title'] not in seen_titles:
                seen_titles.add(item['title'])
                unique_amount_list.append(item)

        amount_list = unique_amount_list


        # # مرتب‌سازی سرویس‌ها
        # first_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - صبحگاهی']
        # second_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - نیم روز']
        # third_item = [item for item in amount_list if item['title'] == 'سرویس درون شهری - عصرگاهی']
        # other_items = [item for item in amount_list if item['title'] not in [
        #     'سرویس درون شهری - صبحگاهی', 'سرویس درون شهری - نیم روز',
        #     'سرویس درون شهری - عصرگاهی', 'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)'
        # ]]
        # last_item = [item for item in amount_list if item['title'] == 'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)']

        # ordered_amount_list = first_item + second_item + third_item + other_items + last_item

        request_time = datetime.datetime.now()
        Ir_holidays = holidays.IR(request_time.year)

        for item in amount_list:
            if request_time.time() >= item['finishHour']:
                pickup_time = request_time + timedelta(days=1)
                while pickup_time.weekday() in Ir_holidays or pickup_time.weekday() == 4:
                    pickup_time += timedelta(days=1)
            else:
                pickup_time = request_time
                while pickup_time.weekday() in Ir_holidays or pickup_time.weekday() == 4:
                    pickup_time += timedelta(days=1)

            item['earliest_pickup_date'] = datetime2jalali(pickup_time).date()

        serialized_data = MyDataSerializer(amount_list, many=True).data

        return JsonResponse(serialized_data, safe=False)


class TotalCalculatePrice(APIView):
    def post(self, request):
        message = ''
        ser_data = PriceDetailSerializer(data=request.data)
        if ser_data.is_valid():
            ser_data.save()
            from_city = ser_data.validated_data.get('from_city')
            to_city = ser_data.validated_data.get('to_city')
            is_multi = ser_data.validated_data.get('is_multi')
            packages = [item.strip() for item in ser_data.validated_data.get('package')[0].split(',')]

            sizes = ser_data.validated_data.get('size')
            if sizes and sizes[0]:
                sizes = [item.strip() for item in sizes[0].split(',')]
            else:
                sizes = None

            counts = [int(count) for count in ser_data.validated_data.get('count')[0].split(',')]
        else:
            return Response({'error': ser_data.errors})

        if City.objects.filter(name=from_city).first() is None or City.objects.filter(name=to_city).first() is None:
            return Response({'message': 'شهر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)

        # تعیین نوع سرویس (درون‌شهری/برون‌شهری)
        if from_city == to_city:
            service_type = Service.objects.filter(s_type='درون شهری').all()
        else:
            service_type = Service.objects.filter(s_type='برون شهری').all()

        cost = 0
        if sizes:
            for i, size in enumerate(sizes):
                size_cost = get_object_or_404(Size, title=size, package_size__title=packages[i])
                cost += float(size_cost.price_co) * int(counts[i])

        size_cost = get_object_or_404(Size, title='کوچک')
        base_cost_co = float(size_cost.price_co)

        if sum(counts) >= 2 and not is_multi:
            decrease_co = sum(counts) - 1 + base_cost_co
        else:
            decrease_co = 0

        # دریافت سرویس‌های عمومی و اختصاصی
        user = request.user
        public_services = service_type.filter(business__isnull=True, is_private=False)
        if user.is_authenticated:
            business_services = service_type.filter(business__real_profile__user=user, is_private=True)
        else:
            business_services = Service.objects.none()

        # ساخت لیست نهایی قیمت‌گذاری
        def create_amount_list(services):
            amount_list = []
            for obj in services:
                total_amount = (int(obj.price) * (sum(counts) + cost)) - (int(obj.price) * decrease_co * 0.3)
                request_time = datetime.datetime.now()
                Ir_holidays = holidays.IR(request_time.year)
                if request_time.time() >= obj.hour:
                    pickup_time = request_time + timedelta(days=1)
                else:
                    pickup_time = request_time

                while pickup_time.weekday() in Ir_holidays or pickup_time.weekday() == 4:
                    pickup_time += timedelta(days=1)

                earliest_pickup_date = datetime2jalali(pickup_time).date()

                amount_list.append({
                    'id': obj.id,
                    'amount': total_amount,
                    'title': obj.title,
                    'finishHour': obj.hour,
                    'delivery_time': obj.delivery_time,
                    'pickup_time': obj.pickup_time,
                    'logo': f'{site}{obj.logo.url}',
                    'earliest_pickup_date': earliest_pickup_date,
                    'message': message
                })
            seen_titles = set()
            unique_amount_list = []
            for item in amount_list:
                if item['title'] not in seen_titles:
                    seen_titles.add(item['title'])
                    unique_amount_list.append(item)

            amount_list = unique_amount_list
            return amount_list
        
        def sort_services(amount_list):
            first = [item for item in amount_list if item['title'] == 'سرویس درون شهری - صبحگاهی']
            second = [item for item in amount_list if item['title'] == 'سرویس درون شهری - نیم روز']
            third = [item for item in amount_list if item['title'] == 'سرویس درون شهری - عصرگاهی']
            other = [item for item in amount_list if item['title'] not in [
                'سرویس درون شهری - صبحگاهی', 'سرویس درون شهری - نیم روز',
                'سرویس درون شهری - عصرگاهی', 'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)'
            ]]
            last = [item for item in amount_list if item['title'] == 'سرویس اختصاصی (بسته غیرمتعارف تا ۲۰ کیلو)']

            return first + second + third + other + last     

        public_amount_list = create_amount_list(public_services)
        public_amount_list = sort_services(public_amount_list)
        business_amount_list = create_amount_list(business_services)

        response_data = {
            'public_services': MyDataSerializer(public_amount_list, many=True).data,
            'business_services': MyDataSerializer(business_amount_list, many=True).data
        }

        return JsonResponse(response_data, safe=False)


class InsurancesView(generics.ListAPIView):
    serializer_class = InsuranceSerializers
    def post(self, request, *args, **kwargs):
        data = InsuranceSerializers(data=self.request.data)
        if data.is_valid():
            val = data.validated_data['value']
            price = data.validated_data['price']
            # val = get_object_or_404(
            #     Value,
            #     id=value
            # )
            # insurance = val.coefficient * val.max_value * 1000000
            val_price=0
            val=int(val)
            if val<1000000 and val>0:
                val_price = 2000
            elif val>=1000000 and val<=20000000:
                val_price = float(val*0.002)
            elif val>20000000 and val<=50000000:
                val_price=float(val*0.003)
            insurance = val_price
            return JsonResponse({'insurance': insurance}, safe=False)
        else:
            return Response(data.errors)
        
class TaxesView(generics.ListAPIView):
    serializer_class = TaxesSerializers
    def post(self, request, *args, **kwargs):
        data = TaxesSerializers(data=self.request.data)
        if data.is_valid():
            val = data.validated_data['value']
            price = data.validated_data['price']
            # val = get_object_or_404(
            #     Value,
            #     id=value
            # )
            # insurance = val.coefficient * val.max_value * 1000000
            val_price=0
            val = int(val)
            if val<1000000 and val>0:
                val_price = 2000
            elif val>=1000000 and val<=20000000:
                val_price = float(val*0.002)
            elif val>20000000 and val<=50000000:
                val_price=float(val*0.003)
            insurance = val_price
            tax = (insurance + price)*tax_co
            return JsonResponse({'tax': tax}, safe=False)
        else:
            return Response(data.errors)

class CheckDateView(APIView):
    def post(self, request, *args, **kwargs):
        choises_date = (request.data['date'])
        choises_date = datetime.datetime.strptime(choises_date, '%Y-%m-%d').date()
        today = datetime.date.today()
        if (choises_date-today).days > 10 or (choises_date-today).days <= 0:
            return Response({'message': 'تاریخ انتخابی نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'تاریخ انتخابی معتبر است'}, status=status.HTTP_200_OK)

def can_fit(n1, n2, n3):
    # Large box dimensions
    L, W, H = 65, 56, 45
    
    # Box dimensions (height, width, depth)
    box1 = (35, 40, 45)
    box2 = (20, 25, 45)
    box3 = (15, 20, 20)
    
    # Total volume calculation
    volume_large_box = L * W * H
    volume_box1 = box1[0] * box1[1] * box1[2]
    volume_box2 = box2[0] * box2[1] * box2[2]
    volume_box3 = box3[0] * box3[1] * box3[2]
    
    # Calculate total volume of all boxes
    total_volume = n1 * volume_box1 + n2 * volume_box2 + n3 * volume_box3
    if total_volume > volume_large_box:
        return False
    
    # 3D grid representation (grid)
    grid = [[[0] * W for _ in range(L)] for _ in range(H)]  # 3D grid initialized to zero
    
    # Function to place a box on the grid
    def place_box(grid, box, count):
        h, w, d = box
        for _ in range(count):  # Loop count times to place the boxes
            placed = False
            for k in range(H - h + 1):  # Iterate over possible positions in height
                for i in range(L - w + 1):  # Iterate over possible positions in length
                    for j in range(W - d + 1):  # Iterate over possible positions in width
                        # Check if the space required for the box is free
                        if all(grid[k+z][i+x][j+y] == 0 for x in range(w) for y in range(d) for z in range(h)):
                            # Mark the grid as occupied
                            for x in range(w):
                                for y in range(d):
                                    for z in range(h):
                                        grid[k+z][i+x][j+y] = 1
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if not placed:
                return False
        return True
    
    # Try to place all boxes
    if not place_box(grid, (box1[0], box1[1], box1[2]), n1):
        return False
    if not place_box(grid, (box2[0], box2[1], box2[2]), n2):
        return False
    if not place_box(grid, (box3[0], box3[1], box3[2]), n3):
        return False
    
    return True

# Create a view to handle the logic and return the result as a plain text response
@api_view(['POST'])
def box_fit_view(request):
    # Example parameters, you can get these from the request (e.g., GET or POST)
    n1 = int(request.data.get('big', 0))
    n2 = int(request.data.get('medium', 0))
    n3 = int(request.data.get('small', 0))
    
    can_fit_result = can_fit(n1, n2, n3)
    
    return Response({'result':can_fit_result})