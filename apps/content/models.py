from django.db import models

from .block_schemas import validate_block_data


class Page(models.Model):
    """A generic structured content page — a department's body, a static page,
    etc. Whatever app needs rich content (departments, faculties, ...) points a
    ForeignKey/OneToOne at one of these instead of storing raw HTML itself."""

    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.slug


class ContentBlock(models.Model):
    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        PARAGRAPH = "paragraph", "Paragraph"
        LIST = "list", "List"
        STAFF_CARD = "staff_card", "Staff card"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"
        GALLERY = "gallery", "Gallery"
        TABLE = "table", "Table"

    page = models.ForeignKey(Page, related_name="blocks", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    block_type = models.CharField(max_length=20, choices=BlockType.choices)
    # {"uz": {...}, "ru": {...}, "en": {...}} — shape of each language's payload
    # depends on block_type, enforced by clean() below. See block_schemas.py.
    data = models.JSONField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["page", "order"], name="unique_block_order_per_page"),
        ]

    def clean(self):
        validate_block_data(self.block_type, self.data)

    def __str__(self) -> str:
        return f"{self.page.slug} #{self.order} ({self.block_type})"
