from django.contrib import admin

from .models import Document, DocumentItem


class DocumentItemInline(admin.TabularInline):
    model = DocumentItem
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title_uz", "slug", "updated_at")
    prepopulated_fields = {"slug": ("title_uz",)}
    inlines = [DocumentItemInline]
