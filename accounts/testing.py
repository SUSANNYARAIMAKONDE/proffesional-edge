"""Shared helpers for the test suites. Not imported by production code."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile

from .models import User

PASSWORD = "S0me-Strong-Pass!"


def make_user(username, role=User.Role.APPLICANT, **extra):
    u = User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD, role=role,
        first_name=username.capitalize(), last_name="Tester", **extra)
    if role == User.Role.STUDENT:
        u.student_id = f"PE-S-T{u.pk:04d}"
        u.save(update_fields=["student_id"])
    return u


def pdf_file(name="doc.pdf", content=b"%PDF-1.4 test file"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class TempPrivateStorageMixin:
    """Redirect private uploads to a throw-away folder for the duration of each test."""

    def setUp(self):
        super().setUp()
        from admissions.models import private_storage
        self._storage = private_storage
        self._tmp = tempfile.mkdtemp()
        self._old = private_storage.__dict__.get("location")
        private_storage.__dict__["location"] = self._tmp
        self.addCleanup(self._restore_storage)

    def _restore_storage(self):
        if self._old is None:
            self._storage.__dict__.pop("location", None)
        else:
            self._storage.__dict__["location"] = self._old
        shutil.rmtree(self._tmp, ignore_errors=True)
