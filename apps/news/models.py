from django.db import models
from django.utils import timezone

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


class NewsPostQuerySet(models.QuerySet):
    def published(self):
        """What the public site may show: not a draft, and not scheduled for later.
        Every public reader of NewsPost (list/detail API, search, sitemap) goes
        through this, so an editor's draft or future-dated post is never exposed."""
        return self.filter(is_published=True, published_at__lte=timezone.now())


class NewsPost(models.Model):
    objects = NewsPostQuerySet.as_manager()

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
    # False = draft: kept in the admin, hidden from the public site. Combined with a
    # future published_at it also gives scheduled publishing for free (see published()).
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title_uz
