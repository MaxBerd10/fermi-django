from django.contrib import admin

from .models import Department, StaffMember


class NeedsTranslationFilter(admin.SimpleListFilter):
    title = "tarjima holati"
    parameter_name = "needs_translation"

    def lookups(self, request, model_admin):
        return (("yes", "Tarjima kerak"), ("no", "Tarjima to'liq"))

    def queryset(self, request, queryset):
        if self.value() not in ("yes", "no"):
            return queryset
        want = self.value() == "yes"
        ids = [obj.id for obj in queryset if obj.needs_translation == want]
        return queryset.filter(id__in=ids)


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
    list_display = ("full_name", "department", "is_head", "order", "needs_translation")
    list_filter = ("department", "is_head", NeedsTranslationFilter)

    @admin.display(description="Tarjima kerak", boolean=True)
    def needs_translation(self, obj):
        return obj.needs_translation
