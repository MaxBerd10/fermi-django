from django.contrib import admin

from .models import VideoClip


@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ("__str__", "order")
