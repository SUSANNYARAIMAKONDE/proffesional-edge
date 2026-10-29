from django.contrib import admin
from .models import Assignment, Course, Enrolment, Module, Resource, Submission


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


class EnrolmentInline(admin.TabularInline):
    model = Enrolment
    extra = 0
    autocomplete_fields = ["student"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "exam_board", "level", "tutor", "active")
    inlines = [ModuleInline, EnrolmentInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "access_level", "published", "version")
    list_filter = ("access_level", "published", "module__course")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_date", "published")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "marks", "released")
