from django.contrib import admin
from django.utils.html import format_html
from .models import PageUrl, OGImage, SchemaImage, HeadTags
import json
import ast
import jdatetime
from datetime import datetime
from django.contrib import admin
from django.utils.html import escape
from django.contrib.admin.models import LogEntry
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime


def format_datetime(value):
    """Converts datetime to Jalali (Shamsi) format."""
    if not value or value == "نامشخص":
        return "نامشخص"
    
    try:
        # Convert to datetime if value is a string
        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        # Convert to local time
        local_dt = localtime(value)

        # Convert Gregorian to Jalali
        jalali_dt = jdatetime.datetime.fromgregorian(datetime=local_dt)

        # Format the output (Customize as needed)
        return jalali_dt.strftime("%Y/%m/%d - %H:%M")  # Example: 1402/12/07 - 14:30
    except Exception:
        return value  # If conversion fails, return original value


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('jalali_action_time', 'user', 'model_name', 'object_repr', 'action_type', 'display_changes')
    list_filter = ('user', 'action_time', 'content_type')  
    search_fields = ('user__username', 'object_repr', 'change_message')

    @admin.display(ordering="content_type__model", description="Model Name")
    def model_name(self, obj):
        return obj.content_type.model
    
    @admin.display(ordering="content_type__model", description="مدل تغییر یافته")
    def model_name(self, obj):
        return obj.content_type.model_class()._meta.verbose_name if obj.content_type else "نامشخص"


    @admin.display(ordering="action_time", description="زمان اقدام")
    def jalali_action_time(self, obj):
        return format_datetime(obj.action_time)

    def action_type(self, obj):
        action_map = {1: "افزودن", 2: "ویرایش", 3: "حذف"}
        return action_map.get(obj.action_flag, "نامشخص")

    def display_changes(self, obj):
        """Display old and new values in Django admin."""
        try:
            change_message = obj.change_message

            # Try parsing JSON (for our custom log format)
            try:
                changes = json.loads(change_message)
            except json.JSONDecodeError:
                return change_message  # If it's not JSON, return as-is

            change_list = []

            if isinstance(changes, dict):  
                # Custom logging format with old and new values
                for field, values in changes.items():
                    
                    old_value = escape(values.get("old", "نامشخص"))[:100]
                    new_value = escape(values.get("new", "نامشخص"))[:100]
                    if isinstance(old_value, str) and ("date" in field or "time" in field or "updated_at" in field):
                        old_value = format_datetime(old_value)
                    if isinstance(new_value, str) and ("date" in field or "time" in field or "updated_at" in field):
                        new_value = format_datetime(new_value)

                    change_list.append(
                    f"<b>{field}</b>: "
                    f"<span style='color: red;'>قدیم: {old_value}</span> ➝<br> "
                    f"<span style='color: green;'>جدید: {new_value}</span>"
                    )

            return mark_safe("<br>".join(change_list)) if change_list else "بدون تغییر"
        except Exception as e:
            return f"خطا در نمایش تغییرات: {str(e)}"  

    display_changes.short_description = "تغییرات"

# ثبت مدل‌های ساده
admin.site.register(OGImage)
admin.site.register(SchemaImage)
admin.site.register(PageUrl)

@admin.register(HeadTags)
class HeadTagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_page_urls', 'created_at', 'updated_at')
    search_fields = ('head_tag',)
    def get_readonly_fields(self, request, obj=None):
        """
        تنها در صورت ویرایش، فیلدهای مربوط به URL تصویر را فقط خواندنی کنیم
        """
        if obj:
            # اگر شیء موجود است (یعنی در حال ویرایش هستیم)
            return ['get_full_og_image_urls', 'get_full_schema_image_urls']
        return []  # در زمان ایجاد هیچ فیلدی به صورت readonly نیست

    def get_page_urls(self, obj):
        urls = [url.page_url for url in obj.page_urls.all()]  # فقط URLها
        return ", ".join(urls)  # بازگرداندن به‌صورت استرینگ
    get_page_urls.short_description = "Page URLs"

    def get_full_og_image_urls(self, obj):
        og_image_urls = obj.get_full_og_image_urls()  # فراخوانی متد جدید برای گرفتن URLها
        return "\n".join(og_image_urls)  # بازگرداندن به‌صورت استرینگ
    get_full_og_image_urls.short_description = "OG Image URLs"

    def get_full_schema_image_urls(self, obj):
        schema_image_urls = obj.get_full_schema_image_urls()  # فراخوانی متد جدید برای گرفتن URLها
        return "\n".join(schema_image_urls)  # بازگرداندن به‌صورت استرینگ
    get_full_schema_image_urls.short_description = "Schema Image URLs"

