from django.db import models

from apps.content.models import Page
from apps.media_lib.models import Image


class NewsCategory(models.Model):
    """The old site groups news into a fixed set of categories (Tadbirlar,
    E'lonlar, ...) — every post carries one via its own API response, so
    this is a real, existing distinction to preserve, not a new feature."""

    slug = models.SlugField(max_length=255, unique=True)
    name_uz = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name_uz


class NewsPost(models.Model):
    slug = models.SlugField(max_length=255, unique=True)

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    excerpt_uz = models.CharField(max_length=500, blank=True)
    excerpt_ru = models.CharField(max_length=500, blank=True)
    excerpt_en = models.CharField(max_length=500, blank=True)

    cover = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    category = models.ForeignKey(NewsCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    page = models.OneToOneField(Page, on_delete=models.PROTECT, related_name="news_post")

    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title_uz
