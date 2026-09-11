from django.contrib import admin

from .models import ContentBlock, Page


class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("slug", "updated_at")
    inlines = [ContentBlockInline]


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ("page", "order", "block_type")
    list_filter = ("block_type",)
