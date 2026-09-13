from django.db import models

from apps.media_lib.models import Document


class Course(models.Model):
    """A course/programme whose class schedule is published as one or more
    downloadable files — see frontend's CourseSchedule type. Not a real
    per-slot timetable (day/time/room/teacher): the old site never had one
    either, just a document library grouped by course (see the PDF-grid UI
    at frontend/src/pages/schedule/page.tsx)."""

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz


class ScheduleFile(models.Model):
    """One downloadable schedule file under a Course — reuses
    media_lib.Document for the actual file (extension validation, size
    tracking) rather than duplicating a FileField here, same as
    Department.logo reusing media_lib.Image."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="schedules")
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="+")

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title_uz
