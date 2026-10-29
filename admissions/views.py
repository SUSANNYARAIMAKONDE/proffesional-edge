from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import ApplicationForm, DecisionForm, DocumentForm
from .letters import build_admission_letter
from .models import Application, ApplicationDocument, StatusHistory


def office_admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *a, **kw):
        if not request.user.is_office_admin:
            raise Http404()  # do not reveal that the page exists
        return view(request, *a, **kw)
    return wrapper


def _set_status(app, new, by, note=""):
    old = app.status
    app.status = new
    app.save(update_fields=["status"])
    StatusHistory.objects.create(application=app, old_status=old, new_status=new, changed_by=by, note=note)


def _notify(app, subject, text):
    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [app.user.email], fail_silently=True)


# ---------- applicant ----------
@login_required
def my_application(request):
    if request.user.role != User.Role.APPLICANT and not hasattr(request.user, "application"):
        return redirect("dashboard")
    app = getattr(request.user, "application", None)
    if app is None:
        return redirect("application_edit")
    return render(request, "admissions/detail.html", {"app": app, "doc_form": DocumentForm()})


@login_required
def application_edit(request):
    app = getattr(request.user, "application", None)
    if app and not app.applicant_can_edit:
        messages.info(request, "This application can no longer be edited.")
        return redirect("my_application")
    form = ApplicationForm(request.POST or None, instance=app, initial={"full_name": request.user.get_full_name()})
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        obj.assign_reference()
        if not app:
            StatusHistory.objects.create(application=obj, new_status=obj.status, changed_by=request.user, note="Draft created")
        messages.success(request, "Draft saved.")
        return redirect("my_application")
    return render(request, "admissions/form.html", {"form": form})


@login_required
def application_submit(request):
    app = get_object_or_404(Application, user=request.user)
    if request.method != "POST" or not app.applicant_can_edit:
        return redirect("my_application")
    resubmission = app.status == Application.Status.INFO
    with transaction.atomic():
        app.submitted_at = timezone.now()
        app.save(update_fields=["submitted_at"])
        _set_status(app, Application.Status.SUBMITTED, request.user, "Resubmitted" if resubmission else "Submitted")
    _notify(app, f"Application received - {app.reference}",
            f"Hello {app.full_name},\n\nWe have received your application. Your reference is {app.reference}.\n"
            "You can track the status by logging in to your account.")
    messages.success(request, f"Application submitted. Your reference is {app.reference}.")
    return redirect("my_application")


@login_required
def document_upload(request):
    app = get_object_or_404(Application, user=request.user)
    if request.method == "POST" and app.applicant_can_edit:
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.application = app
            doc.save()
            messages.success(request, "Document uploaded.")
        else:
            messages.error(request, " ".join(e for errs in form.errors.values() for e in errs))
    return redirect("my_application")


@login_required
def document_download(request, pk):
    doc = get_object_or_404(ApplicationDocument, pk=pk)
    if doc.application.user_id != request.user.id and not request.user.is_office_admin:
        raise Http404()  # permission enforced on the server
    return FileResponse(doc.file.open("rb"), as_attachment=True, filename=f"{doc.application.reference}-{doc.pk}{doc.file.name[-4:]}")


@login_required
def letter_pdf(request, pk):
    app = get_object_or_404(Application, pk=pk)
    if app.user_id != request.user.id and not request.user.is_office_admin:
        raise Http404()
    if app.status != Application.Status.APPROVED:
        raise Http404()
    resp = HttpResponse(build_admission_letter(app), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="admission-letter-{app.reference}.pdf"'
    return resp


# ---------- administrator ----------
@office_admin_required
def review_list(request):
    status = request.GET.get("status", "")
    qs = Application.objects.select_related("user").exclude(status=Application.Status.DRAFT)
    if status:
        qs = qs.filter(status=status)
    rows = [(k, label, Application.objects.filter(status=k).count()) for k, label in Application.Status.choices if k != "draft"]
    return render(request, "admissions/review_list.html",
                  {"apps": qs.order_by("-submitted_at"), "rows": rows, "current": status})


@office_admin_required
def review_detail(request, pk):
    app = get_object_or_404(Application.objects.select_related("user"), pk=pk)
    form = DecisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            new = d["action"]
            if new == Application.Status.APPROVED:
                app.approved_programme = d["approved_programme"]
                app.decided_at = timezone.now()
                u = app.user
                if not u.student_id:
                    u.student_id = f"PE-S-{u.pk:05d}"
                u.role = User.Role.STUDENT
                u.save(update_fields=["student_id", "role"])
            elif new == Application.Status.DECLINED:
                app.decided_at = timezone.now()
            app.admin_note_to_applicant = d["note"]
            app.save()
            _set_status(app, new, request.user, d["note"])
        _notify(app, f"Application update - {app.reference}",
                f"Hello {app.full_name},\n\nYour application status is now: {app.get_status_display()}.\n"
                + (f"\nMessage from Professional Edge:\n{d['note']}\n" if d["note"] else "")
                + "\nLog in to your account for details.")
        messages.success(request, "Decision recorded and applicant notified.")
        return redirect("review_detail", pk=app.pk)
    return render(request, "admissions/review_detail.html", {"app": app, "form": form})
