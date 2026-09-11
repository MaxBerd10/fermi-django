from django.contrib import admin

from .models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("label_uz", "parent", "url", "order")
    list_filter = ("parent",)
