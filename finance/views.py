from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from learning.models import Enrolment
from .forms import CourseInvoiceForm, InvoiceForm, PaymentForm
from .models import AuditEntry, Invoice, Payment
from .permissions import can_view_fees, finance_required, is_finance
from .receipts import build_receipt


def _audit(user, action, detail):
    AuditEntry.objects.create(actor=user, action=action, detail=detail[:300])


@finance_required
def dashboard(request):
    open_invoices = [i for i in Invoice.objects.filter(cancelled=False).select_related("student") if i.balance > 0]
    outstanding = sum(i.balance for i in open_invoices)
    overdue = [i for i in open_invoices if i.due_date < date.today()]
    pending = Payment.objects.filter(status=Payment.Status.PENDING).select_related("invoice__student")
    month = Payment.objects.filter(status=Payment.Status.CONFIRMED, received_on__year=date.today().year,
                                   received_on__month=date.today().month)
    collected = sum(p.amount for p in month)
    return render(request, "finance/dashboard.html", {
        "outstanding": outstanding, "overdue": overdue, "pending": pending, "collected": collected,
        "recent": Payment.objects.select_related("invoice__student")[:8], "audit": AuditEntry.objects.all()[:8]})


@finance_required
def invoice_list(request):
    flt = request.GET.get("state", "")
    invoices = Invoice.objects.select_related("student")
    if request.GET.get("q"):
        q = request.GET["q"]
        invoices = invoices.filter(student__first_name__icontains=q) | invoices.filter(student__last_name__icontains=q) | invoices.filter(student__student_id__icontains=q)
    rows = [i for i in invoices if not flt or i.state.lower() == flt.lower()]
    return render(request, "finance/invoice_list.html", {"invoices": rows, "flt": flt})


@finance_required
def invoice_create(request):
    form = InvoiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inv = form.save(commit=False)
        inv.created_by = request.user
        inv.save()
        _audit(request.user, "invoice_created", f"{inv.number} {inv.amount} for student {inv.student_id}")
        messages.success(request, f"{inv.number} created.")
        return redirect("invoice_detail", pk=inv.pk)
    return render(request, "finance/form.html", {"title": "New invoice", "form": form})


@finance_required
def invoice_course(request):
    form = CourseInvoiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        n = 0
        with transaction.atomic():
            for e in Enrolment.objects.filter(course=d["course"], active=True).select_related("student"):
                already = Invoice.objects.filter(student=e.student, course=d["course"], description=d["description"], cancelled=False).exists()
                if already:
                    continue
                Invoice.objects.create(student=e.student, course=d["course"], description=d["description"], amount=d["amount"],
                                       due_date=d["due_date"], created_by=request.user)
                n += 1
        _audit(request.user, "bulk_invoice", f"{n} invoices for course {d['course'].pk}: {d['description']}")
        messages.success(request, f"{n} invoice(s) created (students already invoiced for this description were skipped).")
        return redirect("invoice_list")
    return render(request, "finance/form.html", {"title": "Invoice all students in a course", "form": form})


@finance_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice.objects.select_related("student"), pk=pk)
    form = PaymentForm(request.POST or None, invoice=inv)
    if request.method == "POST" and not inv.cancelled and form.is_valid():
        p = form.save(commit=False)
        p.invoice, p.recorded_by = inv, request.user
        p.save()
        _audit(request.user, "payment_recorded", f"{inv.number} {p.amount} {p.method} ref {p.reference}")
        messages.success(request, "Payment recorded as pending. Confirm it once the money is verified.")
        return redirect("invoice_detail", pk=inv.pk)
    return render(request, "finance/invoice_detail.html", {"inv": inv, "form": form})


@finance_required
def payment_decide(request, pk, decision):
    p = get_object_or_404(Payment.objects.select_related("invoice"), pk=pk)
    if request.method != "POST" or p.status != Payment.Status.PENDING or decision not in ("confirm", "reject"):
        return redirect("invoice_detail", pk=p.invoice_id)
    with transaction.atomic():
        if decision == "confirm":
            p.status = Payment.Status.CONFIRMED
            p.confirmed_by = request.user
            p.save(update_fields=["status", "confirmed_by"])
            p.receipt_number = f"PE-R-{timezone.now().year}-{p.pk:05d}"
            p.save(update_fields=["receipt_number"])
        else:
            p.status = Payment.Status.REJECTED
            p.confirmed_by = request.user
            p.save(update_fields=["status", "confirmed_by"])
        _audit(request.user, f"payment_{decision}ed" if decision == "confirm" else "payment_rejected", f"{p.invoice.number} payment {p.pk} {p.amount}")
    messages.success(request, "Payment " + ("confirmed and receipt issued." if decision == "confirm" else "rejected."))
    return redirect("invoice_detail", pk=p.invoice_id)


@finance_required
def invoice_cancel(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        if inv.paid_total > 0:
            messages.error(request, "This invoice has confirmed payments and cannot be cancelled. Handle refunds under the refund policy.")
        else:
            inv.cancelled = True
            inv.save(update_fields=["cancelled"])
            _audit(request.user, "invoice_cancelled", inv.number)
            messages.success(request, "Invoice cancelled.")
    return redirect("invoice_detail", pk=inv.pk)


@login_required
def receipt_pdf(request, pk):
    p = get_object_or_404(Payment.objects.select_related("invoice__student"), pk=pk)
    if p.status != Payment.Status.CONFIRMED or not can_view_fees(request.user, p.invoice.student):
        raise Http404()
    resp = HttpResponse(build_receipt(p), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="receipt-{p.receipt_number}.pdf"'
    return resp


@login_required
def fee_statement(request, student_id=None):
    student = request.user if student_id is None else get_object_or_404(User, pk=student_id)
    if not can_view_fees(request.user, student):
        raise Http404()
    invoices = Invoice.objects.filter(student=student, cancelled=False).prefetch_related("payments")
    total_due = sum(i.balance for i in invoices)
    return render(request, "finance/statement.html", {"student": student, "invoices": invoices, "total_due": total_due,
                                                       "staff": is_finance(request.user)})
