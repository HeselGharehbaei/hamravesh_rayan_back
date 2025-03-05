from django.contrib import admin, messages
from django.utils.timezone import now
from datetime import timedelta, datetime
from django.db.models import Sum
from .models import Wallet, IncreaseWalletCo, SettelmentWallet
import pandas as pd
from django.http import HttpResponse
from django.utils.timezone import timezone
from openpyxl import Workbook
import jdatetime  # Import the jdatetime package for Jalali date handling


admin.site.register(Wallet)
admin.site.register(IncreaseWalletCo)

def export_settelments_to_excel(modeladmin, request, queryset):
    # Initialize the queryset with filters
    filtered_queryset = queryset

    created_at_filter = request.GET.get('created_at', None)
    if created_at_filter:
        today = jdatetime.date.today()
        formatted_today = today.strftime('%Y/%m/%d')

        if created_at_filter == 'today':
            filtered_queryset = filtered_queryset.filter(order__pickup_date=formatted_today)

        elif created_at_filter == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = past_7_days.strftime('%Y/%m/%d')
            filtered_queryset = filtered_queryset.filter(
                order__pickup_date__range=(formatted_past_7_days, formatted_today)
            )

        elif created_at_filter == 'this_month':
            current_month = formatted_today[:7]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_month)

        elif created_at_filter == 'this_year':
            current_year = formatted_today[:4]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_year)

    
    updated_at_filter = request.GET.get('updated_at', None)
    if updated_at_filter:
        today = jdatetime.date.today()
        formatted_today = today.strftime('%Y/%m/%d')

        if updated_at_filter == 'today':
            filtered_queryset = filtered_queryset.filter(order__pickup_date=formatted_today)

        elif updated_at_filter == 'past_7_days':
            past_7_days = today - jdatetime.timedelta(days=7)
            formatted_past_7_days = past_7_days.strftime('%Y/%m/%d')
            filtered_queryset = filtered_queryset.filter(
                order__pickup_date__range=(formatted_past_7_days, formatted_today)
            )

        elif updated_at_filter == 'this_month':
            current_month = formatted_today[:7]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_month)

        elif updated_at_filter == 'this_year':
            current_year = formatted_today[:4]
            filtered_queryset = filtered_queryset.filter(order__pickup_date__startswith=current_year)
    # Prepare data for export
    data = []
    for obj in filtered_queryset:
        row = {
            "User": obj.user.username if obj.user else None,
            "Dispatcher Last Name": obj.user.profile.last_name if obj.user and hasattr(obj.user, 'profile') else None,
            "Amount": obj.amount,
            "Settlement": obj.settlement,
            "Tracking Code": obj.tracking_code,
            "Error Message": obj.errormessage,
            "Created At": obj.created_at,
            "Updated At": obj.updated_at,
        }

        # Ensure datetime fields are naive
        for key in ["Created At", "Updated At"]:
            if isinstance(row[key], datetime):
                row[key] = row[key].astimezone(timezone.utc).replace(tzinfo=None)

        data.append(row)

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Create an HTTP response with the appropriate Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="settlement_wallets.xlsx"'

    # Write the DataFrame to the Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Settlements')

    return response

class SettelmentWalletAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'get_dispatcher_last_name',
        'amount',
        'settlement',
        'tracking_code',
        'errormessage',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'user__profile__last_name',
        'amount',
        'settlement',
        'errormessage',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'user__username',
        'user__profile__last_name',
        'amount',
        'settlement',
        'errormessage',
        'created_at',
        'updated_at',
    )
    actions = [export_settelments_to_excel]

    def get_dispatcher_last_name(self, obj):
        return obj.user.profile.last_name  # Access the last_name field through related models

    get_dispatcher_last_name.short_description = 'نام خانوادگی'

    def changelist_view(self, request, extra_context=None):
        # Calculate sums and add to extra_context
        last_30_days = now() - timedelta(days=30)

        sum_last_30_days = SettelmentWallet.objects.filter(
            created_at__gte=last_30_days, settlement=True
        ).aggregate(total=Sum('amount'))['total'] or 0

        sum_all = SettelmentWallet.objects.filter(settlement=True).aggregate(
            total=Sum('amount')
        )['total'] or 0

        extra_context = extra_context or {}
        extra_context['sum_last_30_days'] = sum_last_30_days
        extra_context['sum_all'] = sum_all

        # Add message about sums
        self.message_user(
            request,
            f"Total Settlement (Last 30 Days): {sum_last_30_days} | Total Settlement (All Time): {sum_all}",
            level=messages.INFO,
        )
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(SettelmentWallet, SettelmentWalletAdmin)
