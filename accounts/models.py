from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        APPLICANT = "applicant", "Prospective student"
        STUDENT = "student", "Admitted student"
        PARENT = "parent", "Parent/guardian"
        TUTOR = "tutor", "Tutor"
        ADMIN = "admin_staff", "Administrator"
        FINANCE = "finance", "Finance staff"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=60, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPLICANT)
    student_id = models.CharField(max_length=20, blank=True, unique=True, null=True)

    @property
    def is_office_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN
