from django.contrib import admin

from .models import Faculty


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "order")
    prepopulated_fields = {"slug": ("name_uz",)}
