from django.db import models
from django.utils.translation import gettext as _
from django.utils.text import slugify

from tinymce.models import HTMLField

from core.models import BaseModel,TimeStampMixin


class BlogModel(BaseModel, TimeStampMixin,models.Model):
    image = models.ImageField(upload_to='blog/images/', verbose_name=_('image'))
    side_image = models.ImageField(upload_to='blog/side/images/', verbose_name=_('side image'), null=True, blank=True)
    title = models.CharField(max_length=700, verbose_name=_('title'))
    description = models.TextField(_('description'))
    content = HTMLField()
    slug = models.SlugField(unique=True, blank=True, verbose_name=_('slug'))

    def save(self, *args, **kwargs):
        # Generate a slug if it is not already provided
        if not self.slug:
            self.slug = slugify(f"{self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
