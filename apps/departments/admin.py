from django.contrib import admin

from .models import Department, StaffMember


class StaffMemberInline(admin.TabularInline):
    model = StaffMember
    extra = 0


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "updated_at")
    prepopulated_fields = {"slug": ("name_uz",)}
    inlines = [StaffMemberInline]


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "is_head", "order")
    list_filter = ("department", "is_head")
