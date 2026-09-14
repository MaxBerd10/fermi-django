from django.db import models


class VideoClip(models.Model):
    """One item in the /video gallery -- either a self-hosted file or a
    YouTube embed, matching the old site's own mix (most clips are
    self-hosted; a handful are YouTube links). Exactly one of file/
    youtube_id is set, never both -- see frontend's VideoItem type and
    VideoPage, which already branch the same way."""

    file = models.FileField(upload_to="uploads/videos/clips/%Y/%m/", blank=True)
    youtube_id = models.CharField(max_length=32, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-order", "-id"]

    def __str__(self) -> str:
        return self.youtube_id or (self.file.name if self.file else f"VideoClip #{self.pk}")
