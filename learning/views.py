from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import MarkForm, SubmissionForm
from .models import Assignment, Course, Enrolment, Resource, Submission
from .permissions import can_access_resource, can_view_course, is_tutor_of


@login_required
def student_dashboard(request):
    courses = Course.objects.filter(enrolments__student=request.user, enrolments__active=True, active=True)
    assignments = Assignment.objects.filter(course__in=courses, published=True).order_by("due_date")
    done = set(Submission.objects.filter(student=request.user, assignment__in=assignments).values_list("assignment_id", flat=True))
    rows = [(a, a.id in done) for a in assignments]
    return render(request, "learning/student_dashboard.html", {"courses": courses, "rows": rows, "now": timezone.now()})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not can_view_course(request.user, course):
        raise Http404()
    staff = request.user.is_office_admin or is_tutor_of(request.user, course)
    modules = []
    for m in course.modules.all():
        res = [r for r in m.resources.all() if can_access_resource(request.user, r)]
        modules.append((m, res))
    assignments = course.assignments.all() if staff else course.assignments.filter(published=True)
    return render(request, "learning/course_detail.html", {"course": course, "modules": modules, "assignments": assignments, "staff": staff})


def resource_download(request, pk):
    r = get_object_or_404(Resource, pk=pk)
    if not can_access_resource(request.user, r):
        raise Http404()  # checked on the server, not only hidden in the interface
    if r.link and not r.file:
        return redirect(r.link)
    return FileResponse(r.file.open("rb"), as_attachment=True, filename=f"{r.title[:60]}{r.file.name[-4:]}")


@login_required
def assignment_detail(request, pk):
    a = get_object_or_404(Assignment, pk=pk, published=True)
    if not can_view_course(request.user, a.course) or is_tutor_of(request.user, a.course) or request.user.is_office_admin:
        if is_tutor_of(request.user, a.course) or request.user.is_office_admin:
            return redirect("tutor_course", pk=a.course_id)
        raise Http404()
    sub = Submission.objects.filter(assignment=a, student=request.user).first()
    locked = bool(sub and sub.released)
    form = SubmissionForm(request.POST or None, request.FILES or None, instance=sub)
    if request.method == "POST":
        if locked:
            messages.error(request, "This work has been marked and returned.")
        elif a.is_overdue:
            messages.error(request, "The deadline has passed. Contact your tutor.")
        elif form.is_valid():
            s = form.save(commit=False)
            s.assignment, s.student = a, request.user
            s.save()
            messages.success(request, "Submission received.")
            return redirect("assignment_detail", pk=a.pk)
    return render(request, "learning/assignment_detail.html", {"a": a, "sub": sub, "form": form, "locked": locked})


@login_required
def submission_file(request, pk):
    s = get_object_or_404(Submission, pk=pk)
    if s.student_id != request.user.id and not (request.user.is_office_admin or is_tutor_of(request.user, s.assignment.course)):
        raise Http404()
    if not s.file:
        raise Http404()
    return FileResponse(s.file.open("rb"), as_attachment=True, filename=f"submission-{s.pk}{s.file.name[-4:]}")


@login_required
def tutor_dashboard(request):
    courses = Course.objects.filter(tutor=request.user) if not request.user.is_office_admin else Course.objects.all()
    return render(request, "learning/tutor_dashboard.html", {"courses": courses})


@login_required
def tutor_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not (request.user.is_office_admin or is_tutor_of(request.user, course)):
        raise Http404()
    students = Enrolment.objects.filter(course=course, active=True).select_related("student")
    subs = Submission.objects.filter(assignment__course=course).select_related("assignment", "student").order_by("-submitted_at")
    return render(request, "learning/tutor_course.html", {"course": course, "students": students, "subs": subs})


@login_required
def mark_submission(request, pk):
    s = get_object_or_404(Submission.objects.select_related("assignment__course", "student"), pk=pk)
    course = s.assignment.course
    if not (request.user.is_office_admin or is_tutor_of(request.user, course)):
        raise Http404()
    form = MarkForm(request.POST or None, instance=s, max_marks=s.assignment.max_marks)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.marked_by = request.user
        obj.save()
        messages.success(request, "Marking saved.")
        return redirect("tutor_course", pk=course.pk)
    return render(request, "learning/mark.html", {"s": s, "form": form})
