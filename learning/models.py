import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from admissions.models import private_storage, validate_upload


def resource_path(instance, filename):
    return f"resources/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


def submission_path(instance, filename):
    return f"submissions/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class Course(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    exam_board = models.CharField(max_length=60, blank=True)
    level = models.CharField(max_length=60, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="courses_taught", limit_choices_to={"role": "tutor"})
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Enrolment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrolments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrolments")
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student} in {self.course}"


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=160)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course} / {self.title}"


class Resource(models.Model):
    class Access(models.TextChoices):
        PUBLIC = "public", "Public"
        REGISTERED = "registered", "Registered (verified account)"
        ENROLLED = "enrolled", "Enrolled students"
        TUTOR = "tutor", "Tutor/admin only"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=resource_path, storage=private_storage, validators=[validate_upload], blank=True)
    link = models.URLField(blank=True, help_text="Use instead of a file for videos or external links")
    access_level = models.CharField(max_length=12, choices=Access.choices, default=Access.ENROLLED)
    published = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    uploaded = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=160)
    instructions = models.TextField()
    due_date = models.DateTimeField()
    max_marks = models.PositiveIntegerField(default=100)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.course}: {self.title}"

    @property
    def is_overdue(self):
        return timezone.now() > self.due_date


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True)
    file = models.FileField(upload_to=submission_path, storage=private_storage, validators=[validate_upload], blank=True)
    submitted_at = models.DateTimeField(auto_now=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    released = models.BooleanField(default=False, help_text="Student sees marks/feedback only when released")
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = ("assignment", "student")
