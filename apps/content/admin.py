from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe

from apps.media_lib.models import Document, Image, Video

from .models import ContentBlock, Page


class ContentBlockForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = "__all__"
        widgets = {
            "data": forms.Textarea(attrs={"rows": 14, "style": "font-family: monospace; width: 60em;"}),
        }

    class Media:
        js = ["content/contentblock_admin.js"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].help_text = (
            "Barcha uch til (uz, ru, en) uchun to'ldiring — block turini tanlaganingizda "
            "bo'sh maydon avtomatik to'g'ri namuna bilan to'ldiriladi. image/video/document "
            "bloklari uchun kerakli ID'ni pastdagi ro'yxatdan oling."
        )


def _recent_media_reference() -> str:
    """A quick lookup table for the image_id/video_id/document_id an editor
    needs to type into a block's data — without this, finding an id means
    leaving the page to search the Image/Video/Document admin separately."""
    sections = []
    for label, qs, name_fn in (
        ("Rasmlar (image_id)", Image.objects.order_by("-uploaded_at")[:15], lambda o: o.alt_text or o.file.name.rsplit("/", 1)[-1]),
        ("Videolar (video_id)", Video.objects.order_by("-uploaded_at")[:15], lambda o: o.file.name.rsplit("/", 1)[-1]),
        ("Hujjatlar (document_id)", Document.objects.order_by("-uploaded_at")[:15], lambda o: o.title or o.filename),
    ):
        items = list(qs)
        if not items:
            continue
        rows = "".join(f"<li>#{o.id} — {name_fn(o)}</li>" for o in items)
        sections.append(f"<strong>{label}</strong><ul style='margin-top:2px'>{rows}</ul>")
    return mark_safe("".join(sections)) if sections else "Hozircha yuklangan media yo'q."


class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    form = ContentBlockForm
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("slug", "updated_at")
    readonly_fields = ("media_reference",)
    fields = ("slug", "media_reference")
    inlines = [ContentBlockInline]

    @admin.display(description="Mavjud media (image/video/document bloklari uchun)")
    def media_reference(self, obj):
        return _recent_media_reference()


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    form = ContentBlockForm
    list_display = ("page", "order", "block_type")
    list_filter = ("block_type",)
    readonly_fields = ("media_reference",)
    fields = ("media_reference", "page", "order", "block_type", "data")

    @admin.display(description="Mavjud media (image/video/document bloklari uchun)")
    def media_reference(self, obj):
        return _recent_media_reference()
