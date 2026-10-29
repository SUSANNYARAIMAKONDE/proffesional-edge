from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum

from learning.models import Course


class Invoice(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices")
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=200, help_text="e.g. October 2026 - IGCSE English Language")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    cancelled = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"INV-{self.pk:05d} {self.student}"

    @property
    def number(self):
        return f"INV-{self.pk:05d}"

    @property
    def paid_total(self):
        return self.payments.filter(status=Payment.Status.CONFIRMED).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def committed_total(self):
        return self.payments.exclude(status=Payment.Status.REJECTED).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def balance(self):
        return self.amount - self.paid_total

    @property
    def state(self):
        if self.cancelled:
            return "Cancelled"
        if self.balance <= 0:
            return "Paid"
        if self.due_date < date.today():
            return "Overdue"
        return "Part-paid" if self.paid_total > 0 else "Unpaid"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank transfer"
        ECOCASH = "ecocash", "EcoCash"
        ONEMONEY = "onemoney", "OneMoney"
        INNBUCKS = "innbucks", "InnBucks"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices)
    reference = models.CharField(max_length=80, blank=True, help_text="Bank/mobile-money transaction reference. Never enter PINs or card numbers.")
    received_on = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    receipt_number = models.CharField(max_length=20, blank=True, unique=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_on", "-id"]


class AuditEntry(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=60)
    detail = models.CharField(max_length=300)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-at"]
        verbose_name_plural = "audit entries"
