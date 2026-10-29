import uuid
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

private_storage = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


def validate_upload(f):
    ext = Path(f.name).suffix.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXT:
        raise ValidationError("Only PDF, JPG or PNG files are accepted.")
    if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"File is larger than {settings.MAX_UPLOAD_MB} MB.")


def upload_path(instance, filename):
    # random name: never expose the original filename or database ids in storage paths
    return f"applications/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        REVIEW = "under_review", "Under review"
        INFO = "more_info", "More information required"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        HOLD = "on_hold", "On hold / withdrawn"

    class Board(models.TextChoices):
        ZIMSEC = "zimsec", "ZIMSEC"
        CAMBRIDGE = "cambridge", "Cambridge International"
        EDEXCEL = "edexcel", "Pearson Edexcel"
        OTHER = "other", "Other / not sure"

    class Mode(models.TextChoices):
        ONLINE = "online", "Online"
        HOME = "home", "Home visits"
        BOTH = "both", "Both"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="application")
    reference = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    full_name = models.CharField(max_length=120)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    guardian_email = models.EmailField(blank=True)
    current_school = models.CharField(max_length=160, blank=True)
    level = models.CharField(max_length=80, help_text="e.g. Form 4, IGCSE, AS Level, A Level, Adult learner")
    subjects = models.TextField(help_text="Subjects requested, one per line")
    exam_board = models.CharField(max_length=20, choices=Board.choices, default=Board.CAMBRIDGE)
    learning_mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    timetable_notes = models.TextField(blank=True)
    prior_academic_info = models.TextField(blank=True)

    admin_note_to_applicant = models.TextField(blank=True)
    approved_programme = models.CharField(max_length=200, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference or 'draft'} - {self.full_name}"

    @property
    def age(self):
        t = date.today()
        d = self.date_of_birth
        return t.year - d.year - ((t.month, t.day) < (d.month, d.day))

    @property
    def is_minor(self):
        return self.age < 18

    @property
    def applicant_can_edit(self):
        return self.status in (self.Status.DRAFT, self.Status.INFO)

    def assign_reference(self):
        if not self.reference:
            self.reference = f"PE-{timezone.now().year}-{self.pk:05d}"
            self.save(update_fields=["reference"])


class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="documents")
    purpose = models.CharField(max_length=120, help_text="e.g. Latest school report, ID, proof of level")
    file = models.FileField(upload_to=upload_path, storage=private_storage, validators=[validate_upload])
    uploaded = models.DateTimeField(auto_now_add=True)


class StatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-at"]
