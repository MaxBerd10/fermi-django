from django.contrib import admin

from .models import NewsPost


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title_uz", "slug", "published_at")
    prepopulated_fields = {"slug": ("title_uz",)}
