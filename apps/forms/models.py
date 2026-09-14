from django.db import models

from apps.faculties.models import Faculty
from apps.media_lib.models import Document


class ContactSubmission(models.Model):
    """A /aloqa (contact) form submission -- was previously going
    nowhere at all: frontend/src/api/forms.ts::submitContact posted to
    "forms/contact", which had no Django route until this app, so every
    visitor's message silently vanished on submit."""

    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name}: {self.subject}"


class AcceptanceSubmission(models.Model):
    """A /qabul (admission inquiry) form submission -- same gap as
    ContactSubmission (submitQabul posted to "forms/qabul", also
    404). `category_id` is whatever the form's own "Kimga murojaat"
    dropdown sent (backed by connect-leaders on the public form) --
    stored as a plain id, not a hard FK, since it's just a routing label
    on an inquiry, not a relationship the rest of the schema needs to
    enforce."""

    category_id = models.PositiveIntegerField(null=True, blank=True)
    fish = models.CharField(max_length=255, verbose_name="F.I.Sh.")
    subject = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=255)
    region_id = models.PositiveIntegerField(null=True, blank=True)
    district_id = models.PositiveIntegerField(null=True, blank=True)
    quarter_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Qabul arizasi"

    def __str__(self) -> str:
        return self.fish


class VirtualSubmission(models.Model):
    """A /virtual-qabulxona (virtual reception) form submission -- same
    gap (submitVirtualReception posted to "forms/virtual-reception",
    also 404)."""

    fish = models.CharField(max_length=255, verbose_name="F.I.Sh.")
    faculty = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    region_id = models.PositiveIntegerField(null=True, blank=True)
    district_id = models.PositiveIntegerField(null=True, blank=True)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, blank=True)
    text = models.TextField()
    file = models.ForeignKey(Document, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Virtual qabulxona murojaati"

    def __str__(self) -> str:
        return self.fish
