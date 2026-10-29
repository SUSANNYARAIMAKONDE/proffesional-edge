from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from academics.models import ParentLink
from accounts.models import User
from accounts.testing import make_user
from learning.models import Course, Enrolment
from .models import AuditEntry, Invoice, Payment


class FinanceBase(TestCase):
    def setUp(self):
        self.fin = make_user("fin", User.Role.FINANCE)
        self.boss = make_user("boss", User.Role.ADMIN)
        self.tutor = make_user("tutor1", User.Role.TUTOR)
        self.s1 = make_user("stud1", User.Role.STUDENT)
        self.s2 = make_user("stud2", User.Role.STUDENT)
        self.parent = make_user("parent1", User.Role.PARENT)
        self.parent2 = make_user("parent2", User.Role.PARENT)
        ParentLink.objects.create(parent=self.parent, student=self.s1, verified=True)
        ParentLink.objects.create(parent=self.parent2, student=self.s1, verified=False)
        self.inv = Invoice.objects.create(student=self.s1, description="Oct tuition", amount=Decimal("60.00"),
                                          due_date=date.today() + timedelta(days=10), created_by=self.fin)

    def pay(self, amount="20.00", status="confirmed", method="cash", ref="", receipt=None, invoice=None):
        return Payment.objects.create(invoice=invoice or self.inv, amount=Decimal(amount), method=method, reference=ref,
                                      received_on=date.today(), status=status, receipt_number=receipt)

    def code(self, user, url):
        self.client.logout()
        if user:
            self.client.force_login(user)
        return self.client.get(url).status_code

    def record(self, **kw):
        data = dict(amount="20.00", method="cash", reference="", received_on=date.today().isoformat(), note="")
        data.update(kw)
        self.client.force_login(self.fin)
        return self.client.post(reverse("invoice_detail", args=[self.inv.pk]), data)


class RoleBoundaryTests(FinanceBase):
    def test_only_finance_and_admin_reach_finance_pages(self):
        urls = [reverse("finance_dashboard"), reverse("invoice_list"), reverse("invoice_create"),
                reverse("invoice_course"), reverse("invoice_detail", args=[self.inv.pk])]
        for url in urls:
            for user, code in ((self.fin, 200), (self.boss, 200), (self.s1, 404), (self.parent, 404), (self.tutor, 404), (None, 302)):
                with self.subTest(url=url, user=getattr(user, "username", "anonymous")):
                    self.assertEqual(self.code(user, url), code)

    def test_non_finance_cannot_write(self):
        pay = self.pay(status="pending")
        self.client.force_login(self.s1)
        self.client.post(reverse("payment_decide", args=[pay.pk, "confirm"]))
        self.client.post(reverse("invoice_cancel", args=[self.inv.pk]))
        self.client.post(reverse("invoice_create"), {"student": self.s1.pk, "description": "Free", "amount": "1", "due_date": "2030-01-01"})
        pay.refresh_from_db()
        self.inv.refresh_from_db()
        self.assertEqual(pay.status, "pending")
        self.assertFalse(self.inv.cancelled)
        self.assertEqual(Invoice.objects.count(), 1)


class BalanceAndStateTests(FinanceBase):
    def test_pending_and_rejected_do_not_reduce_balance(self):
        self.pay("20.00", status="pending")
        self.pay("10.00", status="rejected")
        self.assertEqual(self.inv.paid_total, Decimal("0"))
        self.assertEqual(self.inv.balance, Decimal("60.00"))
        self.assertEqual(self.inv.committed_total, Decimal("20.00"))
        self.assertEqual(self.inv.state, "Unpaid")

    def test_states(self):
        self.pay("20.00")
        self.assertEqual(self.inv.state, "Part-paid")
        self.pay("40.00")
        self.assertEqual(self.inv.state, "Paid")
        late = Invoice.objects.create(student=self.s2, description="Old", amount=Decimal("10"), due_date=date.today() - timedelta(days=1))
        self.assertEqual(late.state, "Overdue")
        late.cancelled = True
        self.assertEqual(late.state, "Cancelled")


class PaymentRecordingTests(FinanceBase):
    def test_valid_cash_payment_is_pending_and_attributed(self):
        self.record()
        p = Payment.objects.get()
        self.assertEqual((p.status, p.recorded_by), ("pending", self.fin))
        self.assertTrue(AuditEntry.objects.filter(action="payment_recorded").exists())

    def test_overpayment_rejected_including_pending_amounts(self):
        self.record(amount="100.00")
        self.assertEqual(Payment.objects.count(), 0)
        self.pay("50.00", status="pending")
        self.record(amount="20.00")
        self.assertEqual(Payment.objects.count(), 1)

    def test_non_cash_needs_reference(self):
        self.record(method="bank", reference="")
        self.assertEqual(Payment.objects.count(), 0)

    def test_duplicate_reference_rejected_case_insensitively(self):
        self.pay("10.00", status="pending", method="bank", ref="ABC123")
        self.record(method="bank", reference="abc123")
        self.assertEqual(Payment.objects.count(), 1)

    def test_reference_of_rejected_payment_can_be_reused(self):
        self.pay("10.00", status="rejected", method="ecocash", ref="EC999")
        self.record(method="ecocash", reference="EC999")
        self.assertEqual(Payment.objects.count(), 2)

    def test_cannot_record_against_cancelled_invoice(self):
        self.inv.cancelled = True
        self.inv.save()
        self.record()
        self.assertEqual(Payment.objects.count(), 0)


class ReconciliationTests(FinanceBase):
    def decide(self, pay, decision, user=None):
        self.client.force_login(user or self.fin)
        return self.client.post(reverse("payment_decide", args=[pay.pk, decision]))

    def test_confirm_issues_receipt_and_updates_balance(self):
        p = self.pay("25.00", status="pending")
        self.decide(p, "confirm")
        p.refresh_from_db()
        self.assertEqual(p.status, "confirmed")
        self.assertTrue(p.receipt_number.startswith("PE-R-"))
        self.assertEqual(p.confirmed_by, self.fin)
        self.assertEqual(self.inv.balance, Decimal("35.00"))
        self.assertTrue(AuditEntry.objects.filter(action="payment_confirmed").exists())

    def test_reject_leaves_balance_and_no_receipt(self):
        p = self.pay("25.00", status="pending")
        self.decide(p, "reject")
        p.refresh_from_db()
        self.assertEqual((p.status, p.receipt_number), ("rejected", None))
        self.assertEqual(self.inv.balance, Decimal("60.00"))

    def test_decision_is_final_and_needs_post(self):
        p = self.pay("25.00", status="pending")
        self.client.force_login(self.fin)
        self.client.get(reverse("payment_decide", args=[p.pk, "confirm"]))
        p.refresh_from_db()
        self.assertEqual(p.status, "pending")
        self.decide(p, "confirm")
        p.refresh_from_db()
        first_receipt = p.receipt_number
        self.decide(p, "reject")
        p.refresh_from_db()
        self.assertEqual((p.status, p.receipt_number), ("confirmed", first_receipt))

    def test_unknown_decision_changes_nothing(self):
        p = self.pay("25.00", status="pending")
        self.decide(p, "delete")
        p.refresh_from_db()
        self.assertEqual(p.status, "pending")


class ReceiptAndStatementAccessTests(FinanceBase):
    def setUp(self):
        super().setUp()
        self.confirmed = self.pay("20.00", receipt="PE-R-2026-00001")
        self.pending = self.pay("10.00", status="pending")

    def test_receipt_access_matrix(self):
        url = reverse("receipt_pdf", args=[self.confirmed.pk])
        for user, code in ((self.s1, 200), (self.parent, 200), (self.fin, 200), (self.boss, 200),
                           (self.s2, 404), (self.parent2, 404), (self.tutor, 404), (None, 302)):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.assertEqual(self.code(user, url), code)

    def test_receipt_is_a_pdf_and_pending_has_none(self):
        self.client.force_login(self.s1)
        resp = self.client.get(reverse("receipt_pdf", args=[self.confirmed.pk]))
        self.assertTrue(resp.content.startswith(b"%PDF"))
        self.assertEqual(self.client.get(reverse("receipt_pdf", args=[self.pending.pk])).status_code, 404)

    def test_statement_access_matrix(self):
        url = reverse("child_fees", args=[self.s1.pk])
        for user, code in ((self.s1, 200), (self.parent, 200), (self.fin, 200),
                           (self.s2, 404), (self.parent2, 404), (self.tutor, 404), (None, 302)):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.assertEqual(self.code(user, url), code)

    def test_student_my_fees_shows_only_own_invoices(self):
        Invoice.objects.create(student=self.s2, description="OTHERKID-INVOICE", amount=Decimal("5"), due_date=date.today())
        self.client.force_login(self.s1)
        resp = self.client.get(reverse("my_fees"))
        self.assertContains(resp, "Oct tuition")
        self.assertNotContains(resp, "OTHERKID-INVOICE")


class InvoiceManagementTests(FinanceBase):
    def test_create_invoice_logs_audit_entry(self):
        self.client.force_login(self.fin)
        self.client.post(reverse("invoice_create"), {"student": self.s2.pk, "description": "Nov tuition", "amount": "60.00", "due_date": "2026-11-30"})
        self.assertTrue(Invoice.objects.filter(student=self.s2, description="Nov tuition").exists())
        self.assertTrue(AuditEntry.objects.filter(action="invoice_created").exists())

    def test_zero_or_negative_amount_rejected(self):
        self.client.force_login(self.fin)
        for amt in ("0", "-5"):
            self.client.post(reverse("invoice_create"), {"student": self.s2.pk, "description": "Bad", "amount": amt, "due_date": "2026-11-30"})
        self.assertEqual(Invoice.objects.count(), 1)

    def test_cannot_invoice_non_students(self):
        self.client.force_login(self.fin)
        self.client.post(reverse("invoice_create"), {"student": self.tutor.pk, "description": "Bad", "amount": "10", "due_date": "2026-11-30"})
        self.assertEqual(Invoice.objects.count(), 1)

    def test_cancel_blocked_when_confirmed_payment_exists(self):
        self.pay("20.00")
        self.client.force_login(self.fin)
        self.client.post(reverse("invoice_cancel", args=[self.inv.pk]))
        self.inv.refresh_from_db()
        self.assertFalse(self.inv.cancelled)

    def test_cancel_unpaid_invoice(self):
        self.client.force_login(self.fin)
        self.client.post(reverse("invoice_cancel", args=[self.inv.pk]))
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.cancelled)

    def test_bulk_course_invoicing_is_idempotent(self):
        course = Course.objects.create(title="Bulk Course", tutor=self.tutor)
        Enrolment.objects.create(student=self.s1, course=course)
        Enrolment.objects.create(student=self.s2, course=course)
        Enrolment.objects.create(student=make_user("stud3", User.Role.STUDENT), course=course, active=False)
        self.client.force_login(self.fin)
        data = {"course": course.pk, "description": "Oct bulk", "amount": "60.00", "due_date": "2026-11-30"}
        self.client.post(reverse("invoice_course"), data)
        self.client.post(reverse("invoice_course"), data)
        self.assertEqual(Invoice.objects.filter(description="Oct bulk").count(), 2)

    def test_dashboard_outstanding_total(self):
        self.pay("20.00")
        self.client.force_login(self.fin)
        resp = self.client.get(reverse("finance_dashboard"))
        self.assertEqual(resp.context["outstanding"], Decimal("40.00"))
        self.assertEqual(resp.context["collected"], Decimal("20.00"))
