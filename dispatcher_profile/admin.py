from django.contrib import admin
from .models import *


class DispatcherProfileInline(admin.StackedInline):
    model = DispatcherProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('first_name', 'last_name')  # Add any fields you want to display

class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'confirm', 'created_at', 'updated_at')
    search_fields = ('first_name', 'last_name', 'confirm')
    list_filter = ('confirm','created_at', 'updated_at')

# Registering the CustomUser model with the custom admin class
admin.site.register(DispatcherProfile, DispatcherProfileAdmin)
admin.site.register(Zone_disp)

