from django.contrib import admin
from .models import Application, ApplicationDocument, StatusHistory


class DocInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "status", "exam_board", "submitted_at")
    list_filter = ("status", "exam_board")
    search_fields = ("reference", "full_name", "user__email")
    inlines = [DocInline]


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("application", "old_status", "new_status", "changed_by", "at")
    readonly_fields = [f.name for f in StatusHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
