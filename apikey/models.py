import secrets
from datetime import timedelta

from django.utils import timezone
from django.db import models

from core.models import BaseModel, TimeStampMixin, MyFourDigitModel
from business.models import Business

class ApiKeyModel(MyFourDigitModel, TimeStampMixin,models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, null=True, blank=True)
    key = models.CharField(max_length=64, unique=True, blank=True, null=False)
    expiration_date = models.DateTimeField(blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    get_message = models.BooleanField(default=False)

    def is_expired(self):
        return self.expiration_date < timezone.now()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(days=1826)  # Expire after 5 years
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name