import re
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
import pandas as pd

from dispatcher_profile.models import DispatcherProfile
from .models import Order, QRCode, OrderStatusLogs, ProcessExcel
import jdatetime  # Import the jdatetime package for Jalali date handling
from django.db.models import Q
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.db import models
from django.utils.timezone import is_aware, make_naive






# Function to convert English numbers to Persian numbers
def convert_english_numbers_to_persian(english_number):
    english_to_persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }

    # Replace each English numeral with its Persian equivalent
    persian_number = ''.join(english_to_persian_digits.get(digit, digit) for digit in str(english_number))
    return persian_number

class DispatcherSenderFilter(SimpleListFilter):
    title = 'dispatcher sender'  # Display name for the filter
    parameter_name = 'dispatcher_sender'

    def lookups(self, request, model_admin):
        # Include all dispatchers, even those with confirm=False
        return [(dispatcher.id, dispatcher.last_name) for dispatcher in DispatcherProfile.objects.all()]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected dispatcher sender
        if self.value():
            return queryset.filter(dispatcher_sender__id=self.value())
        return queryset


class DispatcherReceiverFilter(SimpleListFilter):
    title = 'dispatcher receiver'
    parameter_name = 'dispatcher_receiver'

    def lookups(self, request, model_admin):
        # Include all dispatchers, even those with confirm=False
        return [(dispatcher.id, dispatcher.last_name) for dispatcher in DispatcherProfile.objects.all()]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected dispatcher receiver
        if self.value():
            return queryset.filter(dispatcher_reciever__id=self.value())
        return queryset
    
# Admin filter for pickup date
class PickupDateFilter(admin.SimpleListFilter):
    title = _('pickup date')
    parameter_name = 'pickup_date'

    def lookups(self, request, model_admin):
        return [
            ('today', _('Today')),
            ('past_7_days', _('Past 7 days')),
            ('this_month', _('This month')),
            ('this_year', _('This year')),
            ('7_days_after', _('7 days after today')),
            ('one_month_after', _('One month after today')),
            ('one_year_after', _('One year after today')),
        ]

    def queryset(self, request, queryset):
        # Get today's date in Jalali format
        today = jdatetime.date.today()

        # Convert today's date to Persian format (e.g., ۱۴۰۳/۰۷/۲۰)
        formatted_today = today.strftime('%Y/%m/%d')
        persian_today = convert_english_numbers_to_persian(formatted_today)
        
        # Use this Persian date string for filtering
        if self.value() == 'today':
            return queryset.filter(pickup_date=persian_today)
        
        if self.value() == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = convert_english_numbers_to_persian(past_7_days.strftime('%Y/%m/%d'))
            return queryset.filter(pickup_date__range=(formatted_past_7_days, persian_today))
        
        if self.value() == 'this_month':
            return queryset.filter(pickup_date__startswith=persian_today[:7])  # Compare only the year/month part
        
        if self.value() == 'this_year':
            current_year = persian_today[:4]  # Extract the year part
            return queryset.filter(pickup_date__startswith=current_year)
        
        if self.value() == '7_days_after':
            seven_days_after = today + jdatetime.timedelta(days=7)
            formatted_seven_days_after = convert_english_numbers_to_persian(seven_days_after.strftime('%Y/%m/%d'))
            return queryset.filter(pickup_date__range=(persian_today, formatted_seven_days_after))
        
        if self.value() == 'one_month_after':
            one_month_after = today + jdatetime.timedelta(days=30)
            formatted_one_month_after = convert_english_numbers_to_persian(one_month_after.strftime('%Y/%m/%d'))
            return queryset.filter(pickup_date__range=(persian_today, formatted_one_month_after))
        
        if self.value() == 'one_year_after':
            one_year_after = today + jdatetime.timedelta(days=365)
            formatted_one_year_after = convert_english_numbers_to_persian(one_year_after.strftime('%Y/%m/%d'))
            return queryset.filter(pickup_date__range=(persian_today, formatted_one_year_after))

        return queryset
    

def export_orders_to_excel(modeladmin, request, queryset):
    # Initialize the queryset to include the applied filters
    filtered_queryset = queryset

    # Apply custom filters similar to the ones defined in the admin
    pursuit_filter = request.GET.get('pursuit', None)
    if pursuit_filter:
        filtered_queryset = filtered_queryset.filter(pursuit=pursuit_filter)

    user_business_filter = request.GET.get('user_business', None)
    if user_business_filter:
        filtered_queryset = filtered_queryset.filter(user_business__name__icontains=user_business_filter)

    pickup_date_filter = request.GET.get('pickup_date', None)
    if pickup_date_filter:
        today = jdatetime.date.today()
        formatted_today = convert_english_numbers_to_persian(today.strftime('%Y/%m/%d'))
        
        if pickup_date_filter == 'today':
            filtered_queryset = filtered_queryset.filter(pickup_date=formatted_today)

        elif pickup_date_filter == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = convert_english_numbers_to_persian(past_7_days.strftime('%Y/%m/%d'))
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_past_7_days, formatted_today)
            )

        elif pickup_date_filter == 'this_month':
            current_month = formatted_today[:7]  # Extract year/month
            filtered_queryset = filtered_queryset.filter(pickup_date__startswith=current_month)

        elif pickup_date_filter == 'this_year':
            current_year = formatted_today[:4]  # Extract year
            filtered_queryset = filtered_queryset.filter(pickup_date__startswith=current_year)

        elif pickup_date_filter == '7_days_after':
            seven_days_after = today + jdatetime.timedelta(days=7)
            formatted_seven_days_after = convert_english_numbers_to_persian(
                seven_days_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_seven_days_after)
            )

        elif pickup_date_filter == 'one_month_after':
            one_month_after = today + jdatetime.timedelta(days=30)
            formatted_one_month_after = convert_english_numbers_to_persian(
                one_month_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_one_month_after)
            )

        elif pickup_date_filter == 'one_year_after':
            one_year_after = today + jdatetime.timedelta(days=365)
            formatted_one_year_after = convert_english_numbers_to_persian(
                one_year_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_one_year_after)
            )
    dispatcher_sender_filter = request.GET.get('dispatcher_sender', None)
    if dispatcher_sender_filter:
        filtered_queryset = filtered_queryset.filter(dispatcher_sender__id__icontains=dispatcher_sender_filter)

    dispatcher_receiver_filter = request.GET.get('dispatcher_reciever', None)
    if dispatcher_receiver_filter:
        filtered_queryset = filtered_queryset.filter(dispatcher_reciever__id__icontains=dispatcher_receiver_filter)

    created_at_filter = request.GET.get('created_at', None)
    if created_at_filter:
        filtered_queryset = filtered_queryset.filter(created_at__gte=created_at_filter)

    updated_at_filter = request.GET.get('updated_at', None)
    if updated_at_filter:
        filtered_queryset = filtered_queryset.filter(updated_at__gte=updated_at_filter)

    # Convert the filtered queryset to a DataFrame
    data = list(filtered_queryset.values())


    # Make sure datetime fields are timezone-unaware
    for row in data:
        for field in ['created_at', 'updated_at']:
            if field in row and row[field]:
                if isinstance(row[field], str):
                    # Skip conversion for strings
                    continue
                if isinstance(row[field], timezone.datetime):
                    row[field] = row[field].astimezone(timezone.utc).replace(tzinfo=None)
    
    # No need to convert pickup_date because it's a string, just keep it as is
    # No changes to pickup_date field are required
    # Convert the filtered queryset to a list of dictionaries
    data = []
    for obj in filtered_queryset:
        row = {}
        for field in obj._meta.get_fields():
            if field.name== "orderslog":
                continue
            if isinstance(field, models.ForeignKey):
                # Use the related object's __str__ representation
                value = getattr(obj, field.name)
                row[field.name] = str(value) if value else None
            elif isinstance(field, models.DateTimeField):
                # Handle datetime fields to remove timezone information
                value = getattr(obj, field.name)
                row[field.name] = value.astimezone(timezone.utc).replace(tzinfo=None) if value else None
            else:
                row[field.name] = getattr(obj, field.name)
        
        row["service_price"] = obj.service.price if obj.service else None

        # Add computed fields
        val_price = None
        if obj.value is not None:
            value = obj.value
            if value<1000000 and value>0:
                val_price = 2000
            elif value>=1000000 and value<=20000000:
                val_price = float(value*0.002)
            elif value>20000000 and value<=50000000:
                val_price=float(value*0.003)
        row["value_price"] = val_price

        
        data.append(row)
    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create an HTTP response with the appropriate Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="filtered_orders.xlsx"'

    # Write the DataFrame to the Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Orders')

    return response    


def export_orders_to_excel_logestic(modeladmin, request, queryset):
    # Initialize the queryset to include the applied filters
    filtered_queryset = queryset

    # Apply custom filters similar to the ones defined in the admin
    pursuit_filter = request.GET.get('pursuit', None)
    if pursuit_filter:
        filtered_queryset = filtered_queryset.filter(pursuit=pursuit_filter)

    user_business_filter = request.GET.get('user_business', None)
    if user_business_filter:
        filtered_queryset = filtered_queryset.filter(user_business__name__icontains=user_business_filter)

    pickup_date_filter = request.GET.get('pickup_date', None)
    if pickup_date_filter:
        today = jdatetime.date.today()
        formatted_today = convert_english_numbers_to_persian(today.strftime('%Y/%m/%d'))
        
        if pickup_date_filter == 'today':
            filtered_queryset = filtered_queryset.filter(pickup_date=formatted_today)

        elif pickup_date_filter == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = convert_english_numbers_to_persian(past_7_days.strftime('%Y/%m/%d'))
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_past_7_days, formatted_today)
            )

        elif pickup_date_filter == 'this_month':
            current_month = formatted_today[:7]  # Extract year/month
            filtered_queryset = filtered_queryset.filter(pickup_date__startswith=current_month)

        elif pickup_date_filter == 'this_year':
            current_year = formatted_today[:4]  # Extract year
            filtered_queryset = filtered_queryset.filter(pickup_date__startswith=current_year)

        elif pickup_date_filter == '7_days_after':
            seven_days_after = today + jdatetime.timedelta(days=7)
            formatted_seven_days_after = convert_english_numbers_to_persian(
                seven_days_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_seven_days_after)
            )

        elif pickup_date_filter == 'one_month_after':
            one_month_after = today + jdatetime.timedelta(days=30)
            formatted_one_month_after = convert_english_numbers_to_persian(
                one_month_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_one_month_after)
            )

        elif pickup_date_filter == 'one_year_after':
            one_year_after = today + jdatetime.timedelta(days=365)
            formatted_one_year_after = convert_english_numbers_to_persian(
                one_year_after.strftime('%Y/%m/%d')
            )
            filtered_queryset = filtered_queryset.filter(
                pickup_date__range=(formatted_today, formatted_one_year_after)
            )
    dispatcher_sender_filter = request.GET.get('dispatcher_sender', None)
    if dispatcher_sender_filter:
        filtered_queryset = filtered_queryset.filter(dispatcher_sender__id__icontains=dispatcher_sender_filter)

    dispatcher_receiver_filter = request.GET.get('dispatcher_reciever', None)
    if dispatcher_receiver_filter:
        filtered_queryset = filtered_queryset.filter(dispatcher_reciever__id__icontains=dispatcher_receiver_filter)

    created_at_filter = request.GET.get('created_at', None)
    if created_at_filter:
        filtered_queryset = filtered_queryset.filter(created_at__gte=created_at_filter)

    updated_at_filter = request.GET.get('updated_at', None)
    if updated_at_filter:
        filtered_queryset = filtered_queryset.filter(updated_at__gte=updated_at_filter)

    # Convert the filtered queryset to a DataFrame
    data = list(filtered_queryset.values())

    # Make sure datetime fields are timezone-unaware
    for row in data:
        for field in ['created_at', 'updated_at']:
            if field in row and row[field]:
                if isinstance(row[field], str):
                    # Skip conversion for strings
                    continue
                if isinstance(row[field], timezone.datetime):
                    row[field] = row[field].astimezone(timezone.utc).replace(tzinfo=None)
    
    # No need to convert pickup_date because it's a string, just keep it as is
    # No changes to pickup_date field are required
    # Convert the filtered queryset to a list of dictionaries

    data = []
    fields_for_logestic = ['user_business', 'service', 'receiver_zone', 'receiver_district', 'receiver_address', 'receiver_name', 'receiver_phone', 'dispatcher_reciever']

    for obj in filtered_queryset:
        row = {}
        for field_name in fields_for_logestic:
            # Check if the field exists in the model
            if hasattr(obj, field_name):
                value = getattr(obj, field_name, None)

                if isinstance(obj._meta.get_field(field_name), models.ForeignKey):
                    # Handle ForeignKey relationships
                    row[field_name] = str(value) if value else None
                elif isinstance(obj._meta.get_field(field_name), models.DateTimeField):
                    # Handle datetime fields (remove timezone information)
                    row[field_name] = value.astimezone(timezone.utc).replace(tzinfo=None) if value else None
                else:
                    # Handle other field types
                    row[field_name] = value

        # Append the filtered row to the data list
        data.append(row) 
            
        # data.append(row)
        # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create an HTTP response with the appropriate Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="filtered_orders.xlsx"'

    # Write the DataFrame to the Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered logestic Orders')

    return response


class OrderAdmin(admin.ModelAdmin):
    list_display = ('pursuit', 'user_business', 'pickup_date', 'order_number', 'receiver_name', 'receiver_phone', 'receiver_zone', 'tracking_code', 'dispatcher_sender', 'dispatcher_reciever', 'service','created_at', 'updated_at')
    list_filter = ('pursuit', 'user_business', PickupDateFilter, DispatcherSenderFilter, DispatcherReceiverFilter, 'created_at', 'updated_at', 'service__title')
    search_fields = ('pursuit', 'user_business__name', 'pickup_date', 'receiver_name', 'tracking_code', 'order_number', 'dispatcher_sender__last_name', 'dispatcher_reciever__last_name', 'created_at', 'updated_at', 'service__title')
    allowed_edit_fields_log = []
    allowed_edit_fields_crm = ['pickup_date', 'order_description','pursuit','address_description', 'sender_address', 'sender_map_link', 'receiver_address', 'receiver_map_link']


    actions = [export_orders_to_excel, export_orders_to_excel_logestic]
    
    def save_model(self, request, obj, form, change):
        # Skip pickup_date validation for superusers if status is being changed
        if request.user.is_superuser and 'pursuit' in form.changed_data and 'pursuit'=='revoke':
            obj.full_clean(exclude=['pickup_date'])  # Exclude pickup_date validation
            super().save_model(request, obj, form, change)
            return

        # For non-superusers or changes unrelated to status, validate pickup_date
        try:
            obj.full_clean()  # Apply all model-level validations
        except ValidationError as e:
            raise ValidationError(f"Validation error: {e}")

        # Save normally if validation passes
        super().save_model(request, obj, form, change)
    def get_readonly_fields(self, request, obj=None):
    # If the user is not a superuser, restrict all fields except the allowed fields
        if not request.user.is_superuser:
            if request.user.groups.filter(name='logestic').exists():
                delivered_field = ['dispatcher_reciever']
                allowed_edit_fields_log = self.allowed_edit_fields_log[:]

                    # If pursuit is 'delivered', allow editing the delivered_field
                if obj and obj.pursuit == 'waiting for distribution':
                    allowed_edit_fields_log += delivered_field 
                    # Get all the model fields
                all_fields = [field.name for field in self.model._meta.fields]
                # Mark all fields as read-only except the allowed fields
                return [field for field in all_fields if field not in allowed_edit_fields_log]
            if request.user.groups.filter(name='business').exists():
                returned_fields = ['service']
                allowed_edit_fields_crm = self.allowed_edit_fields_crm[:] 
                if obj and obj.pursuit == 'returned':
                    allowed_edit_fields_crm += returned_fields
                # Get all the model fields
                all_fields = [field.name for field in self.model._meta.fields]
                # Mark all fields as read-only except the allowed fields
                return [field for field in all_fields if field not in allowed_edit_fields_crm]
        # If superuser, no fields are read-only
        return super().get_readonly_fields(request, obj)
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if '\u0600' <= search_term <= '\u06FF':
        # Retrieve the database values associated with the Persian labels in pursuit_choices
            pursuit_values = [choice[0] for choice in self.model.pursuit_choises if search_term in choice[1]]

            # Filter queryset by both display labels and database values of pursuit
            queryset |= self.model.objects.filter(
                Q(pursuit__icontains=search_term) | Q(pursuit__in=pursuit_values)
            )
            queryset |= self.model.objects.filter(user_business__name__icontains=search_term)
            queryset |= self.model.objects.filter(pickup_date=search_term)
            queryset |= self.model.objects.filter(tracking_code=search_term)

        return queryset, use_distinct
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "dispatcher":
            obj_id = request.resolver_match.kwargs.get('object_id')  # Get the ID of the current order
            if obj_id:
                # If editing an existing order, include all Dispatchers
                kwargs["queryset"] = DispatcherProfile.objects.all()
            else:
                # If creating a new order, only include active Dispatchers
                kwargs["queryset"] = DispatcherProfile.objects.filter(confirm=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Order, OrderAdmin)

admin.site.register(QRCode)

class DispatcherSenderFilterLog(SimpleListFilter):
    title = 'dispatcher sender'  # Display name for the filter
    parameter_name = 'dispatcher_sender'

    def lookups(self, request, model_admin):
        # Include all dispatchers, even those with confirm=False
        return [(dispatcher.id, dispatcher.last_name) for dispatcher in DispatcherProfile.objects.all()]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected dispatcher sender
        if self.value():
            return queryset.filter(order__dispatcher_sender__id=self.value())
        return queryset


class DispatcherReceiverFilterLog(SimpleListFilter):
    title = 'dispatcher receiver'
    parameter_name = 'dispatcher_receiver'

    def lookups(self, request, model_admin):
        # Include all dispatchers, even those with confirm=False
        return [(dispatcher.id, dispatcher.last_name) for dispatcher in DispatcherProfile.objects.all()]

    def queryset(self, request, queryset):
        # Filter the queryset based on the selected dispatcher receiver
        if self.value():
            return queryset.filter(order__dispatcher_reciever__id=self.value())
        return queryset
    
# Admin filter for pickup date
class PickupDateFilterLog(admin.SimpleListFilter):
    title = _('pickup date')
    parameter_name = 'pickup_date'

    def lookups(self, request, model_admin):
        return [
            ('today', _('Today')),
            ('past_7_days', _('Past 7 days')),
            ('this_month', _('This month')),
            ('this_year', _('This year')),
            ('7_days_after', _('7 days after today')),
            ('one_month_after', _('One month after today')),
            ('one_year_after', _('One year after today')),
        ]

    def queryset(self, request, queryset):
        # Get today's date in Jalali format
        today = jdatetime.date.today()

        # Convert today's date to Persian format (e.g., ۱۴۰۳/۰۷/۲۰)
        formatted_today = today.strftime('%Y/%m/%d')
        persian_today = convert_english_numbers_to_persian(formatted_today)
        
        # Use this Persian date string for filtering
        if self.value() == 'today':
            return queryset.filter(order__pickup_date=persian_today)
        
        if self.value() == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = convert_english_numbers_to_persian(past_7_days.strftime('%Y/%m/%d'))
            return queryset.filter(order__pickup_date__range=(formatted_past_7_days, persian_today))
        
        if self.value() == 'this_month':
            return queryset.filter(order__pickup_date__startswith=persian_today[:7])  # Compare only the year/month part
        
        if self.value() == 'this_year':
            current_year = persian_today[:4]  # Extract the year part
            return queryset.filter(order__pickup_date__startswith=current_year)
        
        if self.value() == '7_days_after':
            seven_days_after = today + jdatetime.timedelta(days=7)
            formatted_seven_days_after = convert_english_numbers_to_persian(seven_days_after.strftime('%Y/%m/%d'))
            return queryset.filter(order__pickup_date__range=(persian_today, formatted_seven_days_after))
        
        if self.value() == 'one_month_after':
            one_month_after = today + jdatetime.timedelta(days=30)
            formatted_one_month_after = convert_english_numbers_to_persian(one_month_after.strftime('%Y/%m/%d'))
            return queryset.filter(order__pickup_date__range=(persian_today, formatted_one_month_after))
        
        if self.value() == 'one_year_after':
            one_year_after = today + jdatetime.timedelta(days=365)
            formatted_one_year_after = convert_english_numbers_to_persian(one_year_after.strftime('%Y/%m/%d'))
            return queryset.filter(order__pickup_date__range=(persian_today, formatted_one_year_after))

        return queryset


def export_orderslog_to_excel(modeladmin, request, queryset):
    # Initialize the queryset with filters
    filtered_queryset = queryset

    # Apply filters based on GET parameters
    pursuit_filter = request.GET.get('pursuit', None)
    if pursuit_filter:
        filtered_queryset = filtered_queryset.filter(order__pursuit=pursuit_filter)

    user_business_filter = request.GET.get('user_business', None)
    if user_business_filter:
        filtered_queryset = filtered_queryset.filter(order__user_business__name__icontains=user_business_filter)

    pickup_date_filter = request.GET.get('pickup_date', None)
    if pickup_date_filter:
        today = jdatetime.date.today()
        formatted_today = today.strftime('%Y/%m/%d')

        if pickup_date_filter == 'today':
            filtered_queryset = filtered_queryset.filter(order__pickup_date=formatted_today)

        elif pickup_date_filter == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = past_7_days.strftime('%Y/%m/%d')
            filtered_queryset = filtered_queryset.filter(
                order__pickup_date__range=(formatted_past_7_days, formatted_today)
            )

        elif pickup_date_filter == 'this_month':
            current_month = formatted_today[:7]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_month)

        elif pickup_date_filter == 'this_year':
            current_year = formatted_today[:4]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_year)

    # Add logic for other filters like dispatcher_sender, created_at, etc.
    dispatcher_sender_filter = request.GET.get('dispatcher_sender', None)
    if dispatcher_sender_filter:
        filtered_queryset = filtered_queryset.filter(order__dispatcher_sender__id__icontains=dispatcher_sender_filter)

    dispatcher_reciever_filter = request.GET.get('dispatcher_receiver', None)
    if dispatcher_reciever_filter:
        filtered_queryset = filtered_queryset.filter(order__dispatcher_reciever__id__icontains=dispatcher_reciever_filter)

    # Prepare data for export
    data = []
    for obj in filtered_queryset:
        # created_at = make_naive(obj.created_at) if is_aware(obj.created_at) else obj.created_at
        # updated_at = make_naive(obj.updated_at) if is_aware(obj.updated_at) else obj.updated_at

        row = {
            "Order ID": obj.order.id if obj.order else None,
            "User Business": obj.order.user_business.name if obj.order and obj.order.user_business else None,
            "Dispatcher Sender": obj.order.dispatcher_sender.last_name if obj.order and obj.order.dispatcher_sender else None,
            "Dispatcher Receiver": obj.order.dispatcher_reciever.last_name if obj.order and obj.order.dispatcher_reciever else None,
            "Pickup Date": obj.order.pickup_date if obj.order else None,
            "Get by Ambassador": obj.get_by_ambassador,
            "Delivered": obj.delivered,
            "Returned": obj.returned,
            "Service Time Difference (Get)": obj.service_time_difference_get,
            "Service Time Difference (Deliver)": obj.service_time_difference_deliver,
            "In Time (Get)": obj.get_intime,
            "In Time (Deliver)": obj.deliver_intime,
            "Created At": obj.created_at,
            "Updated At": obj.updated_at,
        }
        for key, value in row.items():
            if isinstance(value, timezone.datetime):  # Check if the value is a datetime
                if is_aware(value):  # If aware, convert to naive
                    row[key] = make_naive(value)

        data.append(row)

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Create an HTTP response with the appropriate Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="order_status_logs.xlsx"'

    # Write the DataFrame to the Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Order Status Logs')

    return response



@admin.register(OrderStatusLogs)
class OrderStatusLogsAdmin(admin.ModelAdmin):
    list_display = (
        'get_pursuit',
        'get_user_business',
        'order',
        'get_receiver_name', 
        'get_receiver_phone_number' ,
        'get_dispatcher_sender', 
        'get_dispatcher_reciever', 
        'get_pickup_date',
        'get_service_received_time', 
        'get_by_ambassador',
        'get_service_delivery_time',
        'get_receiver_phone_number' ,
        'get_receiver_name',
        'delivered', 
        'returned',
        'service_time_difference_get', 
        'service_time_difference_deliver',
        'get_intime', 
        'deliver_intime', 
        'created_at', 
        'updated_at'
    )
    list_filter = (
        'get_intime',
        'deliver_intime',
        'order__pursuit', 
        'order__user_business', 
        PickupDateFilterLog, 
        DispatcherSenderFilterLog, 
        DispatcherReceiverFilterLog, 
        'created_at', 
        'updated_at',
        # فیلدهای مرتبط با سرویس
        'order__service__pickup_time',
        'order__service__delivery_time',
    )
    # search_fields = (
    #     'get_intime',
    #     'deliver_intime',
    #     'order__tracking_code', 
    #     'order__user_business__name', 
    #     'order__dispatcher_sender__last_name', 
    #     'order__dispatcher_reciever__last_name', 
    #     'order__pickup_date',
        
    # )
    search_fields = (
    # فیلدهای اصلی Order
    'order__tracking_code', 
    'order__pursuit',
    'order__user_business__name',
    'order__dispatcher_sender__last_name', 
    'order__dispatcher_reciever__last_name', 
    'order__receiver_name',
    'order__receiver_phone',
    'order__pickup_date',
    'order__created_at',
    'order__updated_at',

    # فیلدهای مرتبط با زمان و وضعیت
    'get_intime',
    'deliver_intime',
    'service_time_difference_get',
    'service_time_difference_deliver',

    # فیلدهای مرتبط با سرویس
    'order__service__pickup_time',
    'order__service__delivery_time',

    # فیلدهای محاسباتی و وضعیت
    'delivered',
    'returned',
    )


    # Custom methods for related fields
    @admin.display(description='order pursuit')
    def get_pursuit(self, obj):
        if obj.order and obj.order.pursuit:
            return obj.order.get_pursuit_display()  # Use the display method for choices
        return None
    
    @admin.display(description='User Business')
    def get_user_business(self, obj):
        return obj.order.user_business.name if obj.order and obj.order.user_business else None

    @admin.display(description='Dispatcher Sender')
    def get_dispatcher_sender(self, obj):
        return obj.order.dispatcher_sender.last_name if obj.order and obj.order.dispatcher_sender else None

    @admin.display(description='Dispatcher Receiver')
    def get_dispatcher_reciever(self, obj):
        return obj.order.dispatcher_reciever.last_name if obj.order and obj.order.dispatcher_reciever else None

    @admin.display(description='Pickup Date')
    def get_pickup_date(self, obj):
        return obj.order.pickup_date if obj.order else None
    
    @admin.display(description='service recieved time', ordering='service_received_time')
    def get_service_received_time(self, obj):
        return obj.order.service.pickup_time if obj.order else None
    
    @admin.display(description='service deliver time', ordering='service_delivery_time')
    def get_service_delivery_time(self, obj):
        return obj.order.service.delivery_time if obj.order else None
    
    @admin.display(description='receiver phone number')
    def get_receiver_phone_number(self, obj):
        return obj.order.receiver_phone if obj.order else None
    
    @admin.display(description='receiver name')
    def get_receiver_name(self, obj):
        return obj.order.receiver_name if obj.order else None
    

    # Register the action
    actions = [export_orderslog_to_excel]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate the related `service_delivery_time` field
        return qs.annotate(
            service_received_time=models.F('order__service__pickup_time'),
            service_delivery_time=models.F('order__service__delivery_time')
        )

admin.site.register(ProcessExcel)