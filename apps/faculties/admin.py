from django.contrib import admin

from apps.departments.models import StaffMember

from .models import Faculty


class FacultyLeaderInline(admin.TabularInline):
    model = StaffMember
    fk_name = "faculty"
    extra = 0


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "order")
    prepopulated_fields = {"slug": ("name_uz",)}
    inlines = [FacultyLeaderInline]
