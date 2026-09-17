from django.db import models

from apps.media_lib.models import Document


class ResultsPage(models.Model):
    """Singleton heading/announcement text for the /qabul-natijalari page --
    same pattern as apps.site_settings's _SingletonModel (one row, always
    pk=1). Re-editable each admission cycle (dates, confirmed/unconfirmed
    wording) without a code change."""

    heading_uz = models.CharField(max_length=255, blank=True)
    heading_ru = models.CharField(max_length=255, blank=True)
    heading_en = models.CharField(max_length=255, blank=True)

    intro_uz = models.CharField(max_length=500, blank=True)
    intro_ru = models.CharField(max_length=500, blank=True)
    intro_en = models.CharField(max_length=500, blank=True)

    announcement_uz = models.TextField(blank=True)
    announcement_ru = models.TextField(blank=True)
    announcement_en = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return "Qabul natijalari sahifasi"


class ResultCategory(models.Model):
    """A specialty/major whose admission-test results are published as one
    or more downloadable files -- see apps.schedule.Course, the same shape
    for the same reason (a document library grouped by category, not a
    structured per-row dataset)."""

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz


class ResultFile(models.Model):
    """One downloadable results file under a ResultCategory -- reuses
    media_lib.Document for the actual file (extension validation, size
    tracking), same as apps.schedule.ScheduleFile."""

    category = models.ForeignKey(ResultCategory, on_delete=models.CASCADE, related_name="files")
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="+")

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz
