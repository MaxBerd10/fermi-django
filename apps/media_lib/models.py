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
