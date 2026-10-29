from django.contrib import admin
from .models import Programme, Announcement, Enquiry


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "exam_board", "level", "published", "order")
    list_editable = ("published", "order")
    list_filter = ("category", "published")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "created")
    list_editable = ("published",)


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "status", "owner", "created")
    list_filter = ("status", "category")
    list_editable = ("status", "owner")
    search_fields = ("name", "email", "message")
