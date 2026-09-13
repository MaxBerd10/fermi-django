from django.db import models


class Document(models.Model):
    """
    A named collection of documents (e.g. a set of institutional bylaws or
    orders) shown as one accordion page — see frontend's
    /documents/:menuId/:slug route and DocumentDetail type. Short, uniform
    fields per language, same rationale as Department.name_*: these are
    short titles, not long-form prose that would need ContentBlock's
    grow-with-content layout.
    """

    slug = models.SlugField(max_length=255, unique=True)

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title_uz


class DocumentItem(models.Model):
    """One accordion entry within a Document collection — a title plus an
    HTML body, matching DocumentItem's {title, content} shape."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="items")
    slug = models.SlugField(max_length=255)

    title_uz = models.CharField(max_length=255)
    title_ru = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    content_uz = models.TextField(blank=True)
    content_ru = models.TextField(blank=True)
    content_en = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["document", "slug"], name="unique_document_item_slug_per_document")
        ]

    def __str__(self) -> str:
        return self.title_uz
