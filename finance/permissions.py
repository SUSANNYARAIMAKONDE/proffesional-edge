from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import Http404

from academics.models import ParentLink
from accounts.models import User


def is_finance(user):
    return user.is_authenticated and (user.is_office_admin or user.role == User.Role.FINANCE)


def finance_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *a, **kw):
        if not is_finance(request.user):
            raise Http404()
        return view(request, *a, **kw)
    return wrapper


def can_view_fees(user, student):
    """Student sees own fees; a VERIFIED parent sees their child's; finance staff see all. Tutors see none."""
    if not user.is_authenticated:
        return False
    if user.id == student.id or is_finance(user):
        return True
    return ParentLink.objects.filter(parent=user, student=student, verified=True).exists()
