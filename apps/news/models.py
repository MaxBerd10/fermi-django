from django.db import models

from apps.content.models import Page
from apps.media_lib.models import Image


class NewsPost(models.Model):
    slug = models.SlugField(max_length=255, unique=True)

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    excerpt_uz = models.CharField(max_length=500, blank=True)
    excerpt_ru = models.CharField(max_length=500, blank=True)
    excerpt_en = models.CharField(max_length=500, blank=True)

    cover = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    page = models.OneToOneField(Page, on_delete=models.PROTECT, related_name="news_post")

    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title_uz
