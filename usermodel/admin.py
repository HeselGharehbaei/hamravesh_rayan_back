from django.contrib import admin
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'created_at', 'updated_at')
    search_fields = ('username',)
    list_filter = ('created_at', 'updated_at')

# Registering the Business model with the custom admin class
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CustomResetPassword)
admin.site.register(CustomRegisterLoginCode)
# admin_interface.site.register(RefreshToken)


