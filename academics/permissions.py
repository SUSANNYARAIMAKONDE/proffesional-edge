from learning.models import Course
from .models import ParentLink


def can_view_student(user, student):
    if not user.is_authenticated:
        return False
    if user.id == student.id or user.is_office_admin:
        return True
    if ParentLink.objects.filter(parent=user, student=student, verified=True).exists():
        return True
    return Course.objects.filter(tutor=user, enrolments__student=student, enrolments__active=True).exists()
