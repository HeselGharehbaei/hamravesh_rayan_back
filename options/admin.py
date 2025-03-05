from django.contrib import admin
from jalali_date import datetime2jalali, date2jalali
from jalali_date.admin import ModelAdminJalaliMixin
from .models import *

admin.site.register(Package)
admin.site.register(OrderingOption)
admin.site.register(Size)
admin.site.register(Value)


@admin.register(CheckServiceCount)
class CheckServiceCountAdmin(admin.ModelAdmin):
    list_display = ('pickup_date', 'service_title', 'service_type', 'service_count')  # نمایش ستون‌ها
    list_filter = ('pickup_date', 'service_title')  # فیلترگذاری
    search_fields = ('pickup_date', 'service_title')  # امکان جستجو
    ordering = ['pickup_date']  # مرتب‌سازی


# @admin_interface.register(Shipping)
# class FirstModelAdmin(ModelAdminJalaliMixin, admin_interface.ModelAdmin):
#     # show jalali date in list display
#     list_display = ['title',
#                     'company',
#                     'logo',
#                     'earliest_pickup_jalali',
#                     'delivery_time',
#                     'price',
#                     'type',
#                     ]
#
#
#     @admin_interface.display(description='تاریخ تحویل', ordering='earliest_pickup')
#     def earliest_pickup_jalali(self, obj):
#         return datetime2jalali(obj.earliest_pickup).strftime('%a, %d %b %Y %H:%M:%S')


admin.site.register(Vehicle)
admin.site.register(Service)
admin.site.register(Content)
