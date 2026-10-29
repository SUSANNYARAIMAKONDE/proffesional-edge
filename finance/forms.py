from datetime import date
from decimal import Decimal

from django import forms

from accounts.models import User
from learning.models import Course
from .models import Invoice, Payment


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kw):
        super().__init__(format="%Y-%m-%d", **kw)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["student", "course", "description", "amount", "due_date"]
        widgets = {"due_date": DateInput()}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["student"].queryset = User.objects.filter(role=User.Role.STUDENT).order_by("first_name")
        self.fields["student"].label_from_instance = lambda u: f"{u.get_full_name()} ({u.student_id})"

    def clean_amount(self):
        a = self.cleaned_data["amount"]
        if a <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return a


class CourseInvoiceForm(forms.Form):
    course = forms.ModelChoiceField(Course.objects.filter(active=True))
    description = forms.CharField(max_length=200, help_text="e.g. October 2026 tuition")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'), label="Amount per student")
    due_date = forms.DateField(widget=DateInput())


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "reference", "received_on", "note"]
        widgets = {"received_on": DateInput()}

    def __init__(self, *a, invoice=None, **kw):
        super().__init__(*a, **kw)
        self.invoice = invoice
        self.fields["received_on"].initial = date.today()

    def clean_amount(self):
        a = self.cleaned_data["amount"]
        room = self.invoice.amount - self.invoice.committed_total
        if a <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        if a > room:
            raise forms.ValidationError(f"Amount exceeds the remaining balance ({room}).")
        return a

    def clean(self):
        d = super().clean()
        ref, method = d.get("reference"), d.get("method")
        if method and method != "cash":
            if not ref:
                self.add_error("reference", "Enter the transaction reference for non-cash payments.")
            elif Payment.objects.filter(method=method, reference__iexact=ref).exclude(status="rejected").exists():
                self.add_error("reference", "A payment with this reference has already been recorded.")
        return d
