from .models import Enrolment, Resource


def is_tutor_of(user, course):
    return user.is_authenticated and course.tutor_id == user.id


def can_view_course(user, course):
    if not user.is_authenticated:
        return False
    if user.is_office_admin or is_tutor_of(user, course):
        return True
    return Enrolment.objects.filter(student=user, course=course, active=True).exists() and course.active


def can_access_resource(user, r):
    course = r.module.course
    staff = user.is_authenticated and (user.is_office_admin or is_tutor_of(user, course))
    if not r.published and not staff:
        return False
    if r.access_level == Resource.Access.PUBLIC:
        return True
    if not user.is_authenticated:
        return False
    if r.access_level == Resource.Access.REGISTERED:
        return True
    if r.access_level == Resource.Access.ENROLLED:
        return can_view_course(user, course)
    return staff
