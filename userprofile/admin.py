from django.contrib import admin
from .models import *
class RealUserProfileAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','get_username', 'created_at', 'updated_at']
    search_fields = ['first_name','last_name','get_username', 'created_at', 'updated_at']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

admin.site.register(RealUserProfile, RealUserProfileAdmin)
class LegalUserProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name','get_username', 'phone','created_at', 'updated_at']
    search_fields = ['company_name','get_username', 'phone','created_at', 'updated_at']

    def get_username(self, obj):
        return obj.user_admin.username
    get_username.short_description = 'Username'

    
admin.site.register(LegalUserProfile, LegalUserProfileAdmin)
admin.site.register(AgentCompany)