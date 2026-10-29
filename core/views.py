from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import EnquiryForm
from .models import Announcement, Programme


def home(request):
    return render(request, "core/home.html", {
        "programmes": Programme.objects.filter(published=True)[:8],
        "news": Announcement.objects.filter(published=True)[:3],
    })


def programmes(request):
    return render(request, "core/programmes.html", {"programmes": Programme.objects.filter(published=True)})


def contact(request):
    form = EnquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        enquiry = form.save()
        send_mail("We received your enquiry - Professional Edge",
                  f"Hello {enquiry.name},\n\nThank you for contacting Professional Edge. We will respond shortly.",
                  settings.DEFAULT_FROM_EMAIL, [enquiry.email], fail_silently=True)
        if settings.STAFF_NOTIFY_EMAIL:
            send_mail(f"New enquiry: {enquiry.get_category_display()}",
                      f"From: {enquiry.name} <{enquiry.email}>\n\n{enquiry.message}",
                      settings.DEFAULT_FROM_EMAIL, [settings.STAFF_NOTIFY_EMAIL], fail_silently=True)
        messages.success(request, "Thank you - your enquiry has been sent.")
        return redirect("contact")
    return render(request, "core/contact.html", {"form": form})


def simple_page(template):
    def view(request):
        return render(request, template)
    return view
