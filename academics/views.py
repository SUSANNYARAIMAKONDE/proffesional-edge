from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from learning.models import Course, Enrolment
from learning.permissions import can_view_course, is_tutor_of
from .forms import LessonForm, TutorAssignmentForm, TutorResourceForm
from .models import Attendance, Lesson, ParentLink, Quiz, QuizAttempt
from .permissions import can_view_student
from .reports import build_report, report_pdf


def _tutor_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not (request.user.is_office_admin or is_tutor_of(request.user, course)):
        raise Http404()
    return course


# ---------------- student ----------------
@login_required
def timetable(request, student_id=None):
    student = request.user if student_id is None else get_object_or_404(User, pk=student_id)
    if not can_view_student(request.user, student):
        raise Http404()
    lessons = (Lesson.objects.filter(course__enrolments__student=student, course__enrolments__active=True,
                                     start__gte=timezone.now() - timedelta(hours=2))
               .exclude(status="cancelled").select_related("course").distinct().order_by("start"))
    return render(request, "academics/timetable.html", {"student": student, "lessons": lessons})


@login_required
def quiz_detail(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, published=True)
    if not can_view_course(request.user, quiz.course) or request.user.role != User.Role.STUDENT:
        raise Http404()
    attempt = QuizAttempt.objects.filter(quiz=quiz, student=request.user).first()
    now = timezone.now()
    is_open = quiz.open_at <= now <= quiz.close_at
    if request.method == "POST":
        if attempt:
            messages.error(request, "You have already submitted this quiz.")
        elif not is_open:
            messages.error(request, "This quiz is not open.")
        else:
            answers, score = {}, 0
            for q in quiz.questions.all():
                a = request.POST.get(f"q{q.id}", "")
                answers[str(q.id)] = a
                if a == q.correct:
                    score += q.marks
            QuizAttempt.objects.create(quiz=quiz, student=request.user, answers=answers, score=score)
            messages.success(request, "Quiz submitted.")
        return redirect("quiz_detail", pk=quiz.pk)
    return render(request, "academics/quiz.html", {"quiz": quiz, "attempt": attempt, "is_open": is_open,
                                                   "questions": quiz.questions.all()})


@login_required
def report(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    if not can_view_student(request.user, student):
        raise Http404()
    return render(request, "academics/report.html", {"student": student, "rows": build_report(student)})


@login_required
def report_download(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    if not can_view_student(request.user, student):
        raise Http404()
    resp = HttpResponse(report_pdf(student, build_report(student)), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="progress-report-{student.student_id or student.pk}.pdf"'
    return resp


# ---------------- parent ----------------
@login_required
def parent_dashboard(request):
    links = ParentLink.objects.filter(parent=request.user, verified=True).select_related("student")
    return render(request, "academics/parent_dashboard.html", {"links": links})


@login_required
def child_view(request, student_id):
    student = get_object_or_404(User, pk=student_id)
    if not ParentLink.objects.filter(parent=request.user, student=student, verified=True).exists():
        raise Http404()
    held = Attendance.objects.filter(student=student).select_related("lesson__course").order_by("-lesson__start")[:15]
    return render(request, "academics/child.html", {"student": student, "attendance": held, "rows": build_report(student)})


# ---------------- tutor ----------------
@login_required
def tutor_lessons(request, pk):
    course = _tutor_course(request, pk)
    form = LessonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        lesson = form.save(commit=False)
        lesson.course = course
        lesson.save()
        messages.success(request, "Lesson added.")
        return redirect("tutor_lessons", pk=course.pk)
    return render(request, "academics/tutor_lessons.html", {"course": course, "form": form, "lessons": course.lessons.all()})


@login_required
def attendance_register(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=pk)
    course = _tutor_course(request, lesson.course_id)
    students = [e.student for e in Enrolment.objects.filter(course=course, active=True).select_related("student")]
    existing = {a.student_id: a.status for a in lesson.attendance.all()}
    if request.method == "POST":
        valid = {k for k, _ in Attendance.Status.choices}
        for s in students:
            val = request.POST.get(f"s{s.id}")
            if val in valid:
                Attendance.objects.update_or_create(lesson=lesson, student=s, defaults={"status": val})
        if lesson.status == "scheduled":
            lesson.status = "held"
            lesson.save(update_fields=["status"])
        messages.success(request, "Attendance saved.")
        return redirect("tutor_lessons", pk=course.pk)
    rows = [(s, existing.get(s.id, "present")) for s in students]
    return render(request, "academics/attendance.html", {"lesson": lesson, "rows": rows, "choices": Attendance.Status.choices})


@login_required
def tutor_resource_add(request, pk):
    course = _tutor_course(request, pk)
    form = TutorResourceForm(request.POST or None, request.FILES or None, course=course)
    if request.method == "POST" and form.is_valid():
        r = form.save(commit=False)
        r.uploaded_by = request.user
        r.save()
        messages.success(request, "Resource added.")
        return redirect("tutor_course", pk=course.pk)
    return render(request, "academics/simple_form.html", {"title": f"Add resource - {course.title}", "form": form, "multipart": True, "back": course.pk})


@login_required
def tutor_assignment_add(request, pk):
    course = _tutor_course(request, pk)
    form = TutorAssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        a = form.save(commit=False)
        a.course = course
        a.save()
        messages.success(request, "Assignment created.")
        return redirect("tutor_course", pk=course.pk)
    return render(request, "academics/simple_form.html", {"title": f"New assignment - {course.title}", "form": form, "multipart": False, "back": course.pk})
