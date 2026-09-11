from django.db import models

from apps.content.models import Page
from apps.media_lib.models import Image


class Faculty(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    name_uz = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)
    logo = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    page = models.OneToOneField(Page, on_delete=models.PROTECT, related_name="faculty")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name_uz
