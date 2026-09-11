from django.db import models


class MenuItem(models.Model):
    """
    Site navigation tree. `url` is a plain path/href for now (e.g.
    "/departments/38/akusherlik-va-ginekologiya-kafedrasi") rather than a
    polymorphic reference into content models — simplest thing that works,
    and still just as easy to render as the old site's menu API.
    """

    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    label_uz = models.CharField(max_length=255)
    label_ru = models.CharField(max_length=255)
    label_en = models.CharField(max_length=255)
    url = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.label_uz
