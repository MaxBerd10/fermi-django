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


class SiteText(models.Model):
    """An admin-edited replacement for one interface text (a button, a heading, a footer line, a home-page paragraph).

    The default wording of every such text lives in the frontend's translation files (src/i18n/local/<lang>/common.ts),
    keyed like "home.heroTitle". A row here overrides it for the languages whose field is not blank; a blank field
    means "keep the default for that language". Deleting the row restores the defaults.
    """

    key = models.CharField(max_length=120, unique=True)
    text_uz = models.TextField(blank=True)
    text_ru = models.TextField(blank=True)
    text_en = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key


class HomeItem(models.Model):
    """One entry of a list on the home page that used to be hard-coded in the frontend: a partner link, a project
    card, a student quote, a headline figure or a "why us" card (`section`). The fields are deliberately generic; each
    section uses the ones it needs (see HOME_SECTION_FIELDS in admin_api/home_views.py and src/pages/home/components).

    `image_path` holds a built-in picture shipped with the frontend (/images/projects/x.jpg); `image` is one the
    editors uploaded, and wins when both are set. A blank language falls back to Uzbek when the list is served."""

    PARTNER = "partner"
    PROJECT = "project"
    VOICE = "voice"
    FACT = "fact"
    WHY = "why"
    SECTION_CHOICES = [
        (PARTNER, "Hamkorlar"),
        (PROJECT, "Loyihalar"),
        (VOICE, "Talabalar fikri"),
        (FACT, "Raqamlar"),
        (WHY, "Nega biz"),
    ]

    section = models.CharField(max_length=20, choices=SECTION_CHOICES, db_index=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    subtitle_uz = models.CharField(max_length=255, blank=True)
    subtitle_ru = models.CharField(max_length=255, blank=True)
    subtitle_en = models.CharField(max_length=255, blank=True)
    text_uz = models.TextField(blank=True)
    text_ru = models.TextField(blank=True)
    text_en = models.TextField(blank=True)
    value = models.CharField(max_length=40, blank=True)
    url = models.CharField(max_length=500, blank=True)
    icon = models.CharField(max_length=60, blank=True)
    image = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    image_path = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["section", "order", "id"]

    def __str__(self) -> str:
        return f"{self.section}: {self.title_uz or self.text_uz[:40] or self.value}"
