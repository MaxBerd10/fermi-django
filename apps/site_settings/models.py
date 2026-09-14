from django.db import models

from apps.media_lib.models import Image


class _SingletonModel(models.Model):
    """One row, always id=1 -- matches the admin panel's own singleton
    forms (SingletonFormPage.tsx) for setting/logo/counter: there's
    exactly one site-wide settings/logo/counter, not a list of them."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSetting(_SingletonModel):
    phone = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    faks = models.CharField(max_length=255, blank=True)
    address_uz = models.CharField(max_length=500, blank=True)
    address_ru = models.CharField(max_length=500, blank=True)
    address_en = models.CharField(max_length=500, blank=True)

    def __str__(self) -> str:
        return "Site settings"


class SiteLogo(_SingletonModel):
    image = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    subtitle_uz = models.CharField(max_length=255, blank=True)
    subtitle_ru = models.CharField(max_length=255, blank=True)
    subtitle_en = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return "Site logo"


class SiteCounter(_SingletonModel):
    professor_teachers = models.PositiveIntegerField(default=0)
    students = models.PositiveIntegerField(default=0)
    graduaters = models.PositiveIntegerField(default=0)
    book_fund = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return "Site counters"


class SocialNetwork(models.Model):
    title = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, help_text="e.g. ri-telegram-line")
    url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class UsefulSite(models.Model):
    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    image = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz


class HomeBanner(models.Model):
    """Admin's "Bosh sahifa banneri" (corusel) resource. No page component
    currently reads these back (Hero.tsx has no real carousel data source
    -- see its own comment) so this has no public consumer yet, same as
    UsefulSite did before ContactMap started using it; kept as a plain
    list model rather than skipped since it's cheap and self-contained."""

    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    image = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    content_uz = models.TextField(blank=True)
    content_ru = models.TextField(blank=True)
    content_en = models.TextField(blank=True)
    status = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz or f"Banner #{self.pk}"
