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
    name from their photo). full_name/title are language-invariant (a person's
    name doesn't translate); bio is the one field that does.
    """

    department = models.ForeignKey(Department, related_name="staff", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    bio_uz = models.TextField(blank=True)
    bio_ru = models.TextField(blank=True)
    bio_en = models.TextField(blank=True)
    photo = models.ForeignKey(Image, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    is_head = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.full_name
