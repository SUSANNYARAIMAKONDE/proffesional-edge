from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm
from .models import User

SALT = "pe-email-verify"


def _send_verification(user):
    token = signing.dumps(user.pk, salt=SALT)
    link = settings.SITE_URL + reverse("verify_email", args=[token])
    send_mail(
        "Verify your Professional Edge account",
        f"Hello {user.first_name},\n\nPlease confirm your email to activate your account:\n{link}\n\n"
        "This link expires in 3 days. If you did not register, ignore this email.",
        settings.DEFAULT_FROM_EMAIL, [user.email],
    )


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        first, _, last = d["full_name"].strip().partition(" ")
        user = User.objects.create_user(
            username=d["email"], email=d["email"], password=d["password1"],
            first_name=first, last_name=last, phone=d["phone"], country=d["country"],
            role=User.Role.APPLICANT, is_active=False,
        )
        _send_verification(user)
        return render(request, "accounts/check_email.html", {"email": user.email})
    return render(request, "accounts/register.html", {"form": form})


def verify_email(request, token):
    try:
        pk = signing.loads(token, salt=SALT, max_age=3 * 24 * 3600)
        user = User.objects.get(pk=pk)
    except (signing.BadSignature, User.DoesNotExist):
        return render(request, "accounts/verify_result.html", {"ok": False})
    user.is_active = True
    user.save(update_fields=["is_active"])
    return render(request, "accounts/verify_result.html", {"ok": True})


@login_required
def dashboard(request):
    u = request.user
    if u.is_office_admin:
        return redirect("review_list")
    if u.role == User.Role.APPLICANT:
        return redirect("my_application")
    if u.role == User.Role.STUDENT:
        return redirect("student_dashboard")
    if u.role == User.Role.TUTOR:
        return redirect("tutor_dashboard")
    if u.role == User.Role.PARENT:
        return redirect("parent_dashboard")
    if u.role == User.Role.FINANCE:
        return redirect("finance_dashboard")
    return render(request, "accounts/dashboard.html")
