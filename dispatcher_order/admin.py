import random
from django.contrib import admin

from dispatcher_order.models import CodeGenerateModel


@admin.register(CodeGenerateModel)
class CodeGenerateModelAdmin(admin.ModelAdmin):
    list_display = ('business', 'code')
    actions = ['regenerate_code']
    list_display = ('business', 'code')

    def save_model(self, request, obj, form, change):
        if not obj.code:
            while True:
                code = random.randint(1111, 9999)
                if not CodeGenerateModel.objects.filter(code=code).exists():
                    obj.code = code
                    break
        super().save_model(request, obj, form, change)

    def regenerate_code(self, request, queryset):
        for obj in queryset:
            obj.code = random.randint(1111, 9999)
            obj.save()
        