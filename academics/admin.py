from django.contrib import admin
from .models import Attendance, Lesson, ParentLink, Question, Quiz, QuizAttempt


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "open_at", "close_at", "published", "results_released")
    inlines = [QuestionInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "start", "mode", "status")
    list_filter = ("course", "status")


@admin.register(ParentLink)
class ParentLinkAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "verified", "note", "created")
    list_editable = ("verified",)
    autocomplete_fields = ["parent", "student"]


admin.site.register(Attendance)
admin.site.register(QuizAttempt)
