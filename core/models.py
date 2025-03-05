import os
from django.db import models
from django.utils.translation import gettext as _
from uuid import uuid4
from django.db.models import QuerySet, Manager, Q
from django.utils import timezone
import os


class BaseModel(models.Model):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid4)

    class Meta:
        abstract = True


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created_at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated_at'))

    class Meta:
        abstract = True


class SoftQuerySet(QuerySet):
    def delete(self):
        return self.update(is_deleted = True, deleted_at = timezone.now())  
    

class SoftManager(Manager):
    def get_queryset(self) -> QuerySet:
        return SoftQuerySet(self.model, self._db).filter(Q(is_deleted=False))    
  

class SoftDeleteModel(models.Model):
    objects = SoftManager()

    is_deleted = models.BooleanField(null=True, blank=True, editable=False, db_index=True, default=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False, db_index=True)


    def delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        

    class Meta:
        abstract = True    


from django.db import models
import string
import random
import re
from django.core.exceptions import ValidationError
from .utils.constant import site

def validate_four_digit(value):
    if len(value) != 4 or not re.match(r'^[A-Z0-9]{4}$', value):
        raise ValidationError(f'{value} is not a valid 4-character alphanumeric string.')

class MyFourDigitModel(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=4,
        validators=[validate_four_digit],
        unique=True,
        blank=True,
        editable=False  # این فیلد دیگر در پنل مدیریت نمایش داده نمی‌شود
    )

    class Meta:
        abstract = True  # این مدل انتزاعی است

    def save(self, *args, **kwargs):
        # Generate unique ID automatically if not already set
        if not self.id:
            self.id = self.generate_unique_id()
        super().save(*args, **kwargs)

    def generate_unique_id(self):
        characters = string.digits + string.ascii_uppercase  # اعداد و حروف بزرگ
        while True:
            new_id = ''.join(random.choices(characters, k=4))  # شناسه 4 کاراکتری الفبایی-عددی
            if not type(self).objects.filter(id=new_id).exists():
                return new_id


class PageUrl(TimeStampMixin):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    page_url = models.CharField(max_length=255, verbose_name=_("Page URL"))

    class Meta:
        verbose_name = _("Page URL")
        verbose_name_plural = _("Page URLs")

    def __str__(self):
        return self.page_url


class OGImage(TimeStampMixin):
    image = models.ImageField(upload_to='og_images/', verbose_name=_("OG Image"))
    alt_text = models.CharField(max_length=255, verbose_name=_("Alt Text"), blank=True)

    def __str__(self):
        return os.path.basename(self.image.name)  # فقط نام فایل بدون مسیر


class SchemaImage(TimeStampMixin):
    image = models.ImageField(upload_to='schema_images/', verbose_name=_("Schema Image"))
    alt_text = models.CharField(max_length=255, verbose_name=_("Alt Text"), blank=True)

    def __str__(self):
        return os.path.basename(self.image.name)  # فقط نام فایل بدون مسیر


class HeadTags(TimeStampMixin):
    page_urls = models.ManyToManyField(PageUrl, related_name="head_tags", verbose_name=_("Page URLs"), blank=True)
    head_tag = models.TextField(verbose_name=_("Head Tag"), blank=True)
    og_images = models.ManyToManyField(OGImage, related_name="head_tags", verbose_name=_("OG Images"), blank=True)
    schema_images = models.ManyToManyField(SchemaImage, related_name="head_tags", verbose_name=_("Schema Images"), blank=True)

    def __str__(self):
        return ", ".join([url.page_url for url in self.page_urls.all()])
    

    def get_full_og_image_urls(self):
        # اضافه کردن پیشوند به URL هر تصویر OG
        return [f"{site}{img.image.url}" for img in self.og_images.all()]

    def get_full_schema_image_urls(self):
        # اضافه کردن پیشوند به URL هر تصویر Schema
        return [f"{site}{img.image.url}" for img in self.schema_images.all()]
    

    class Meta:
        verbose_name = _("Head Tag")
        verbose_name_plural = _("Head Tags")
