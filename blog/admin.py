from django.contrib import admin
from .models import BlogModel

class BlogModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'created_at', 'updated_at')

admin.site.register(BlogModel, BlogModelAdmin)