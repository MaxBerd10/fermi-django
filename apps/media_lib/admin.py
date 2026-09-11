from django.contrib import admin

from .models import Document, Image, Video


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("file", "width", "height", "uploaded_at")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("file", "poster", "uploaded_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "filename", "file_size", "uploaded_at")
