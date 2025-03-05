from django.contrib import admin
from .models import AddressNote

class AddressNoteAdmin(admin.ModelAdmin):
    search_fields = ['title', 'name']
    list_display = ('title', 'address', 'zone', 'district', 'name','map_link', 'created_at', 'updated_at')
admin.site.register(AddressNote, AddressNoteAdmin)
