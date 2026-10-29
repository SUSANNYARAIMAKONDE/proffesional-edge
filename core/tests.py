from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Enquiry, Programme


class PublicSiteTests(TestCase):
    def test_public_pages_load(self):
        for name in ("home", "programmes", "contact", "privacy", "terms"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_only_published_programmes_are_shown(self):
        Programme.objects.create(name="Visible Course", category="humanities", published=True)
        Programme.objects.create(name="Hidden Draft Course", category="sciences", published=False)
        resp = self.client.get(reverse("programmes"))
        self.assertContains(resp, "Visible Course")
        self.assertNotContains(resp, "Hidden Draft Course")

    @override_settings(STAFF_NOTIFY_EMAIL="staff@example.com")
    def test_enquiry_is_stored_and_both_emails_sent(self):
        resp = self.client.post(reverse("contact"), {
            "name": "Parent One", "email": "p1@example.com", "phone": "", "category": "admissions",
            "message": "How do I enrol?", "privacy": "on"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual({tuple(m.to) for m in mail.outbox}, {("p1@example.com",), ("staff@example.com",)})

    def test_honeypot_and_missing_consent_are_rejected(self):
        base = {"name": "Bot", "email": "bot@example.com", "category": "other", "message": "spam"}
        self.client.post(reverse("contact"), dict(base, privacy="on", website="http://spam.example"))
        self.client.post(reverse("contact"), base)
        self.assertEqual(Enquiry.objects.count(), 0)


class ManagementCommandTests(TestCase):
    def test_seed_programmes_is_idempotent_and_unpublished(self):
        from django.core.management import call_command
        from io import StringIO
        call_command("seed_programmes", stdout=StringIO())
        n = Programme.objects.count()
        self.assertGreater(n, 0)
        self.assertFalse(Programme.objects.filter(published=True).exists())
        call_command("seed_programmes", stdout=StringIO())
        self.assertEqual(Programme.objects.count(), n)

    def test_export_data_writes_csv_without_passwords(self):
        import csv
        import os
        import tempfile
        from io import StringIO
        from django.core.management import call_command
        from accounts.testing import make_user
        make_user("exportme")
        with tempfile.TemporaryDirectory() as tmp:
            call_command("export_data", out=tmp, stdout=StringIO())
            with open(os.path.join(tmp, "users.csv"), newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            self.assertNotIn("password", rows[0])
            self.assertIn("exportme", [r[rows[0].index("username")] for r in rows[1:]])
            for name in ("applications", "enrolments", "invoices", "payments", "attendance"):
                self.assertTrue(os.path.exists(os.path.join(tmp, f"{name}.csv")))
