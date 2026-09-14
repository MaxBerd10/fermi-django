from django.contrib import admin

from .models import AcceptanceSubmission, ContactSubmission, VirtualSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "phone", "email", "is_read", "created_at")
    list_filter = ("is_read",)


@admin.register(AcceptanceSubmission)
class AcceptanceSubmissionAdmin(admin.ModelAdmin):
    list_display = ("fish", "subject", "phone", "email", "is_read", "created_at")
    list_filter = ("is_read",)


@admin.register(VirtualSubmission)
class VirtualSubmissionAdmin(admin.ModelAdmin):
    list_display = ("fish", "faculty", "phone", "email", "is_read", "created_at")
    list_filter = ("is_read", "faculty")
