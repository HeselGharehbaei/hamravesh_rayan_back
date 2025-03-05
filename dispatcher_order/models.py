from django.db import models
from django.utils.translation import gettext as _

from core.models import TimeStampMixin
from business.models import Business

class CodeGenerateModel(TimeStampMixin, models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(verbose_name=_('code'), max_length=5, null=True, blank=True)

    def __str__(self):
        return self.business.name if self.business else "No Business"