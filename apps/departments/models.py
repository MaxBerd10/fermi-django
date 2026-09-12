from django.core.exceptions import ValidationError
from django.db import models

from apps.content.models import Page
from apps.media_lib.models import Image


class Department(models.Model):
    """
    A kafedra/department. Short fields (name, short description) get one real
    column per language — simplest, most queryable option for exactly 3 fixed
    languages. The long-form body (history, staff-adjacent prose, everything
    that used to be one giant HTML blob) lives in a Page of ContentBlocks
    instead, so language differences in text length can never break layout —
    each block just grows or shrinks with its own content.
    """

    slug = models.SlugField(max_length=255, unique=True)

    name_uz = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)

    logo = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    page = models.OneToOneField(Page, on_delete=models.PROTECT, related_name="department")
    faculty = models.ForeignKey(
        "faculties.Faculty", null=True, blank=True, on_delete=models.SET_NULL, related_name="departments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name_uz


class StaffMember(models.Model):
    """
    A real, structured row per staff member — not scraped out of an <img> tag
    followed by a name in the next paragraph (the old site's approach, which is
    why a stray <hr> or a misplaced paragraph could silently detach someone's
    name from their photo). full_name gets one column per language too, same
    as title/bio: the old site's real content spells names in each language's
    own script (e.g. "Siddiqov Obidjon" in uz, "Сиддиков Обиджон" in ru), not
    just a transliteration-invariant string.

    Belongs to exactly one of department or faculty — a kafedra's staff list
    and a faculty's dekanat/leadership list are the same shape of data (photo,
    name, title, bio, contact details), so one model covers both instead of
    duplicating it.
    """

    department = models.ForeignKey(
        Department, related_name="staff", on_delete=models.CASCADE, null=True, blank=True
    )
    faculty = models.ForeignKey(
        "faculties.Faculty", related_name="leaders", on_delete=models.CASCADE, null=True, blank=True
    )
    full_name_uz = models.CharField(max_length=255)
    full_name_ru = models.CharField(max_length=255, blank=True)
    full_name_en = models.CharField(max_length=255, blank=True)
    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    bio_uz = models.TextField(blank=True)
    bio_ru = models.TextField(blank=True)
    bio_en = models.TextField(blank=True)
    # A short "what they do" line, distinct from the fuller bio above — e.g. a
    # rector/dean card shows both a one-line role summary and a longer
    # biography. Left blank (not fed through needs_translation below) until
    # this is actually backfilled with real content; an empty line just
    # doesn't render, it isn't a broken/missing translation.
    activity_uz = models.TextField(blank=True)
    activity_ru = models.TextField(blank=True)
    activity_en = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=255, blank=True)
    reception_days_uz = models.CharField(max_length=255, blank=True)
    reception_days_ru = models.CharField(max_length=255, blank=True)
    reception_days_en = models.CharField(max_length=255, blank=True)
    photo = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    is_head = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def clean(self):
        if bool(self.department_id) == bool(self.faculty_id):
            raise ValidationError("A staff member must belong to exactly one of department or faculty.")

    def __str__(self) -> str:
        return self.full_name_uz

    @property
    def needs_translation(self) -> bool:
        """See ContentBlock.needs_translation — same idea: a bio, title, or
        name that's byte-identical across two of the three languages is
        almost certainly a fallback copy, not a genuine independent
        translation/transliteration."""
        return (
            len({self.bio_uz, self.bio_ru, self.bio_en}) < 3
            or len({self.title_uz, self.title_ru, self.title_en}) < 3
            or len({self.full_name_uz, self.full_name_ru, self.full_name_en}) < 3
        )
