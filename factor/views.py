from datetime import datetime
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
import jdatetime
from core.utils.constant import tax_co
from business.models import Business
from options.models import Size
from order.models import Order
from userprofile.models import LegalUserProfile, RealUserProfile
from .models import FactorCounter


class FactorView(APIView):
    def get(self, request, *args, **kwargs):
        tracking_code = self.kwargs['tracking_code']
        
        orders = Order.objects.filter(tracking_code=tracking_code, payment_status=True)
        response_data = []
        final_price = 0
        # Get the current Jalali date
        today = jdatetime.date.today()
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            user_name = legal.company_name
        elif real:
            user_name = f'{real.first_name} {real.last_name}'
        else:
            return Response({'message': 'پروفایل یافت نشد'})
        if orders:
            for order in orders:
                user_business = order.user_business
                if not user_business.bill:
                    return Response({'message': 'درخواست فاکتور برای این کسب و کار ثبت نشده'}, status=status.HTTP_400_BAD_REQUEST)
                #start counter
                total_fa_counter = FactorCounter.objects.order_by('created_at').last()
                if total_fa_counter:
                    fa_counter = FactorCounter.objects.filter(tracking_code=tracking_code).first()
                    if fa_counter:
                        counter = fa_counter.count
                    else:
                        counter = total_fa_counter.count + 1
                        FactorCounter.objects.create(tracking_code=tracking_code, count=counter)

                else:
                    counter = 1
                    FactorCounter.objects.create(tracking_code=tracking_code, count=counter)
                str_counter = str(counter)
                zero_count = 5 - len(str_counter)
                # end counter
                str_with0_counter = '0'*zero_count + str_counter
                postal_code = user_business.postal_code
                economic_number = user_business.economic_number
                registration_number = user_business.registration_number
                national_code = user_business.national_code
                address = user_business.address
                phone = user_business.phone
                description = order.service.title
                order_id = order.id
                count = order.count
                # package = order.package.title
                package = 'بسته'
                size = order.size.title
                val = order.value
                val = int(val)
                val_price=0
                if val<1000000 and val>0:
                    val_price = 2000
                elif val>=1000000 and val<=20000000:
                    val_price = float(val*0.002)
                elif val>20000000 and val<=50000000:
                    val_price=float(val*0.003)
                insurance = val_price
                # insurance = int(order.value.max_value) * float(order.value.coefficient) * 10**6
                unity_price = (float(order.size.price_co*int(order.service.price))) + int(order.service.price)
                if count>=2:
                    base_price_for_size = float(Size.objects.filter(title='کوچک').first().price_co)
                    total_price = (((float(order.size.price_co)*int(order.service.price)) + int(order.service.price)) * count) - ((count-1) * base_price_for_size * int(order.service.price) * 0.3)
                else:
                    total_price = ((float(order.size.price_co)*int(order.service.price)) + int(order.service.price)) * count

                tax = total_price*tax_co
                total_price_withtax = total_price + tax
                insurance_tax = insurance*tax_co
                insurance_withtax = insurance_tax + insurance

                if final_price == 0:
                    final_price = insurance_withtax + total_price_withtax
                else:
                    final_price += total_price_withtax
                
                response_data.append({
                    'date': str(today).replace('-', '/'),
                    'counter': str_with0_counter,
                    'user_name': user_name,
                    'order_id': order_id,
                    'tracking_code': tracking_code,
                    'postal_code': postal_code,
                    'economic_number': economic_number,
                    'registration_number': registration_number,
                    'national_code': national_code,
                    'address': address,
                    'phone':phone,
                    'count': count,
                    'package': package,
                    'size': size,
                    'description': description,
                    # 'insurance': insurance,
                    'unity_price':unity_price*10,
                    'total_price': total_price*10,
                    'total_price_withtax': total_price_withtax*10,
                    'tax': tax*10,
                    'insurance': insurance*10,
                    'insurance_tax': insurance_tax*10,
                    'sum_insurance_tax': insurance_withtax*10,
                    'final_price': final_price*10,
                })
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)


class FactorMultiView(APIView):
    def get(self, request, *args, **kwargs):
        order_number = self.kwargs['order_number']
        
        orders_N = Order.objects.filter(order_number=order_number, payment_status=True)
        tracking_codes = orders_N.values_list('tracking_code', flat=True).distinct()
        response_data = []
        all_total_price = 0
        all_final_price = 0
        all_total_price_withtax = 0
        insurance_withtax = 0
        count = 0
        # Get the current Jalali date
        today = jdatetime.date.today()
        user = self.request.user
        legal = LegalUserProfile.objects.filter(user_admin=user).first()
        real = RealUserProfile.objects.filter(user=user).first()
        if legal:
            user_name = legal.company_name
        elif real:
            user_name = f'{real.first_name} {real.last_name}'
        else:
            return Response({'message': 'پروفایل یافت نشد'})
        for tracking_code in tracking_codes:
            orders = Order.objects.filter(tracking_code=tracking_code)
            order = orders.last()
            user_business = order.user_business
            if not user_business.bill:
                return Response({'message': 'درخواست فاکتور برای این کسب و کار ثبت نشده'}, status=status.HTTP_400_BAD_REQUEST)
            #start counter
            total_fa_counter = FactorCounter.objects.order_by('created_at').last()
            if total_fa_counter:
                fa_counter = FactorCounter.objects.filter(tracking_code=order_number).first()
                if fa_counter:
                    counter = fa_counter.count
                else:
                    counter = total_fa_counter.count + 1
                    FactorCounter.objects.create(tracking_code=order_number, count=counter)

            else:
                counter = 1
                FactorCounter.objects.create(tracking_code=order_number, count=counter)
            str_counter = str(counter)
            zero_count = 5 - len(str_counter)
            # end counter
            str_with0_counter = '0'*zero_count + str_counter
            postal_code = user_business.postal_code
            economic_number = user_business.economic_number
            registration_number = user_business.registration_number
            national_code = user_business.national_code
            address = user_business.address
            phone = user_business.phone
            description = order.service.title
            order_id = order.id
            order_number = order.order_number
            count += sum(orderc.count for orderc in orders)
            # package = order.package.title
            package = 'بسته'
            # size = order.size.title
            val = order.value
            val = int(val)
            val_price=0
            if val<1000000 and val>0:
                val_price = 2000
            elif val>=1000000 and val<=20000000:
                val_price = float(val*0.002)
            elif val>20000000 and val<=50000000:
                val_price=float(val*0.003)
            insurance = val_price
            # insurance = int(order.value.max_value) * float(order.value.coefficient) * 10**6
            # unity_price = (float(order.size.price_co*int(order.service.price))) + int(order.service.price)
            # if count>=2:
            #     base_price_for_size = float(Size.objects.filter(title='کوچک').first().price_co)
            #     total_price = (((float(order.size.price_co)*int(order.service.price)) + int(order.service.price)) * count) - ((count-1) * base_price_for_size * int(order.service.price) * 0.3)
            # else:
            #     total_price = ((float(order.size.price_co)*int(order.service.price)) + int(order.service.price)) * count
            total_price = order.total_price
            tax = total_price*tax_co
            # total_price_withtax = total_price + tax
            insurance_tax = insurance*tax_co
            insurance_withtax = insurance_tax + insurance

            all_total_price += total_price
        
        all_final_price = all_total_price 
        all_total_price_without_ins = all_total_price - insurance_withtax
        response_data.append({
            'date': str(today).replace('-', '/'),
            'counter': str_with0_counter,
            'user_name': user_name,
            'order_id': order_number,
            'tracking_code': order_number,
            'postal_code': postal_code,
            'economic_number': economic_number,
            'registration_number': registration_number,
            'national_code': national_code,
            'address': address,
            'phone':phone,
            'count': count,
            'package': package,
            # 'size': size,
            'description': description,
            'unity_price':(all_total_price_without_ins/count)*10,
            'total_price': all_total_price_without_ins*10,
            'total_price_withtax': all_total_price_without_ins*10,
            'tax': tax*10,
            'insurance': insurance*10,
            'insurance_tax': insurance_tax*10,
            'sum_insurance_tax': insurance_withtax*10,
            'final_price': all_final_price*10,
        })
        return Response(response_data, status=status.HTTP_200_OK)