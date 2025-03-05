from django.contrib import admin
from .models import *
from django.db import models
from jalali_date_new.fields import JalaliDateTimeField
from jalali_date_new.widgets import AdminJalaliDateTimeWidget, AdminJalaliTimeWidget, AdminJalaliDateWidget


class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

# Registering the Business model with the custom admin class
admin.site.register(Business, BusinessAdmin)

admin.site.register(BusinessType)

  
@admin.register(BusinessShowCase)
class AdminModel(admin.ModelAdmin):
	formfield_overrides = {
        models.DateTimeField: 
        {
            'form_class': JalaliDateTimeField,
            "widget": AdminJalaliDateTimeWidget,
        },
    }


# from django import forms
# from .models import BusinessShowCase

# class BusinessShowCaseAdminForm(forms.ModelForm):
#     class Meta:
#         model = BusinessShowCase
#         fields = '__all__'
#         widgets = {
#             'expire_date': AdminJalaliDateWidget,  # نمایش تقویم جلالی برای تاریخ
#             'expire_time': forms.TimeInput(attrs={'type': 'time'}),  # نمایش ساعت با input نوع time
#         }

# @admin.register(BusinessShowCase)
# class BusinessShowCaseAdmin(admin.ModelAdmin):
#     form = BusinessShowCaseAdminForm
