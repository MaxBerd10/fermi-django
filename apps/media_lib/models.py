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
