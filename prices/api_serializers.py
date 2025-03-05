from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import serializers
from options.models import Service, Size
from core.utils.constant import tax_co


class PricingSerializer(serializers.Serializer):  
    small_size_count = serializers.CharField(default= '0', allow_blank=False,)
    medium_size_count = serializers.CharField(default= '0', allow_blank=False,)
    big_size_count = serializers.CharField(default= '0', allow_blank=False,)
    value= serializers.CharField(default= '0', allow_blank=False,)
    service= serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=True)
    
    def validate(self, validated_data):
        value = validated_data['value']
        value = int(value)
        if value<1000000 and value>0:
            val_price = 2000
        elif value>=1000000 and value<=20000000:
            val_price = float(value*0.002)
        elif value>20000000 and value<=50000000:
            val_price=float(value*0.003)
        else:
            raise serializers.ValidationError('ارزش نامعتبر است') 
        small_size_count = int(validated_data['small_size_count'])
        medium_size_count = int(validated_data['medium_size_count'])
        big_size_count= int(validated_data['big_size_count'])  
        service = validated_data['service']
        if not Service.objects.filter(id= service.id).filter:
            raise serializers.ValidationError("سرویس یافت نشد")  
        service_price = service.price
            #check size count is existed 
        size_list = [{'کوچک':small_size_count}, {'متوسط':medium_size_count}, {'بزرگ':big_size_count}]     
        if small_size_count==0 and medium_size_count==0 and big_size_count==0:
            raise serializers.ValidationError('حداقل یکی ازفیلدهای تعداد بسته ها باید غیر صفر باشد')
        if small_size_count == 0:
            size_list.remove({'کوچک':small_size_count})
        if medium_size_count == 0:
            size_list.remove({'متوسط':medium_size_count})
        if big_size_count == 0:
            size_list.remove({'بزرگ':big_size_count})          
        total_box_count= small_size_count+medium_size_count+big_size_count
        decrease_count= 0
        if total_box_count >=2:
            decrease_count= total_box_count -1
        on_small_size_price= float(service_price) * (1 + float(Size.objects.filter(title='کوچک').first().price_co))    
        small_size_price = float(service_price) * (1 + float(Size.objects.filter(title='کوچک').first().price_co)) * small_size_count         
        medium_size_price = float(service_price) * (1 + float(Size.objects.filter(title='متوسط').first().price_co)) * medium_size_count
        big_size_price = float(service_price) * (1 + float(Size.objects.filter(title='بزرگ').first().price_co)) * big_size_count
        main_total_price = (small_size_price + medium_size_price + big_size_price) - (on_small_size_price * decrease_count * 0.3)
        total_price= (main_total_price+ val_price)*(1+tax_co)    
        
        return {"total_price": total_price}