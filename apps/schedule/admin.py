from django.contrib import admin

from .models import Course, ScheduleFile


class ScheduleFileInline(admin.TabularInline):
    model = ScheduleFile
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title_uz", "order")
    inlines = [ScheduleFileInline]
