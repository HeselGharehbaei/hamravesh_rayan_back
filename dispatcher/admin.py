from django.contrib import admin
from django.utils.translation import gettext as _
from dispatcher_profile.admin import DispatcherProfileInline
from .models import *

class DispatcherAdmin(admin.ModelAdmin):
    inlines = [DispatcherProfileInline]  # Add the inline to the Dispatcher admin
    list_display = ('username', 'first_name', 'last_name','created_at', 'updated_at')
    search_fields = ('username', 'created_at', 'updated_at')

    # Method to get the first name from the inline model
    def first_name(self, obj):
        return obj.profile.first_name if hasattr(obj, 'profile') else '-'

    # Method to get the last name from the inline model
    def last_name(self, obj):
        return obj.profile.last_name if hasattr(obj, 'profile') else '-'

    first_name.short_description = _("first_name")  # Custom label (translation will apply if defined)
    last_name.short_description = _("last_name")  
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(DispatcherAdmin, self).get_inline_instances(request, obj)
    

admin.site.register(Dispatcher, DispatcherAdmin)
admin.site.register(DispatcherEnterCode)
