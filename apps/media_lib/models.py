import os

from django.core.validators import FileExtensionValidator
from django.db import models


class Image(models.Model):
    """
    A single uploaded image with its REAL dimensions computed by Pillow at
    upload time (width_field/height_field below) — never guessed from
    whatever width an editor typed into a rich-text box. This is what closes
    the "460px looked like a logo" bug from the old site: display size is a
    frontend/CSS decision made from real data, not a backend guess.
    """

    file = models.ImageField(upload_to="uploads/%Y/%m/", width_field="width", height_field="height")
    width = models.PositiveIntegerField(editable=False, null=True)
    height = models.PositiveIntegerField(editable=False, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.file.name} ({self.width}x{self.height})"


class Video(models.Model):
    """
    A single uploaded video with an explicit, editor-chosen poster frame —
    the real fix for the old site's "video looks black until you press play"
    bug. That bug was worked around there with a preload="metadata" + seek
    hack because no real poster frame existed; here a poster is just a
    required field, so the frontend never has to fake one.
    """

    file = models.FileField(upload_to="uploads/videos/%Y/%m/")
    poster = models.ForeignKey(Image, on_delete=models.PROTECT, related_name="video_posters")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.file.name


class Document(models.Model):
    """
    A downloadable file. Rendered as a plain download/view link, not an
    embedded iframe viewer: the old site's iframe viewer was the subject of
    a recurring "PDF takes too long to open" complaint that months of
    investigation never pinned to an actual bug — a link sidesteps the
    whole failure class instead of trying to reproduce a fragile embedded
    viewer here. PDF is the common case (bylaws, council/journal archives);
    xlsx is also real — every one of the old site's class-schedule files
    (see ScheduleFile) is an .xlsx, never a PDF.
    """

    file = models.FileField(
        upload_to="uploads/documents/%Y/%m/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "xlsx"])],
    )
    title = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(editable=False, default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def filename(self) -> str:
        return os.path.basename(self.file.name)

    def __str__(self) -> str:
        return self.title or self.filename


class GalleryPhoto(models.Model):
    """
    A single photo in the public photo gallery — the old site's gallery is a
    flat, uncaptioned stream of campus/event photos (confirmed against its
    live API: every one of 218 existing entries has an empty title), not
    albums, so this deliberately doesn't group photos into anything.
    Captions are still per-language here (blank until/unless someone adds
    one) rather than a single shared field, for the same reason every other
    piece of real content in this project is: a caption written for one
    language is not automatically correct copied into another.
    """

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="+")
    caption_uz = models.CharField(max_length=255, blank=True)
    caption_ru = models.CharField(max_length=255, blank=True)
    caption_en = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-order", "-id"]

    def __str__(self) -> str:
        return self.caption_uz or f"Gallery photo #{self.pk}"
