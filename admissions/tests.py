from datetime import date

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.testing import TempPrivateStorageMixin, make_user, pdf_file
from .models import Application, ApplicationDocument, StatusHistory


def payload(**kw):
    d = dict(full_name="Rudo Dube", date_of_birth="2005-03-04", guardian_name="", guardian_phone="", guardian_email="",
             current_school="", level="A Level", subjects="Psychology", exam_board="cambridge", learning_mode="online",
             timetable_notes="", prior_academic_info="")
    d.update(kw)
    return d


class AdmissionsBase(TempPrivateStorageMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.boss = make_user("boss", User.Role.ADMIN)

    def draft_for(self, user, **kw):
        self.client.force_login(user)
        self.client.post(reverse("application_edit"), payload(**kw))
        return Application.objects.get(user=user)


class ApplicationFlowTests(AdmissionsBase):
    def test_draft_save_and_reference(self):
        app = self.draft_for(self.alice)
        self.assertEqual(app.status, Application.Status.DRAFT)
        self.assertTrue(app.reference.startswith("PE-"))

    def test_minor_needs_guardian_details(self):
        self.client.force_login(self.alice)
        minor_dob = f"{date.today().year - 15}-01-01"
        self.client.post(reverse("application_edit"), payload(date_of_birth=minor_dob))
        self.assertFalse(Application.objects.filter(user=self.alice).exists())
        self.client.post(reverse("application_edit"), payload(date_of_birth=minor_dob, guardian_name="Mr Dube", guardian_phone="+263771111111"))
        self.assertTrue(Application.objects.filter(user=self.alice).exists())

    def test_submit_records_status_and_emails_applicant(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.SUBMITTED)
        self.assertIsNotNone(app.submitted_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertGreaterEqual(StatusHistory.objects.filter(application=app).count(), 2)

    def test_submitted_application_cannot_be_edited(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        self.client.post(reverse("application_edit"), payload(full_name="Changed Name"))
        app.refresh_from_db()
        self.assertEqual(app.full_name, "Rudo Dube")

    def test_more_info_reopens_application_for_editing(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        self.client.force_login(self.boss)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "more_info", "note": "Please add school report"})
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.INFO)
        self.client.force_login(self.alice)
        self.client.post(reverse("application_edit"), payload(prior_academic_info="Report added"))
        app.refresh_from_db()
        self.assertEqual(app.prior_academic_info, "Report added")


class DocumentTests(AdmissionsBase):
    def upload(self, user, f, purpose="School report"):
        self.client.force_login(user)
        return self.client.post(reverse("document_upload"), {"purpose": purpose, "file": f})

    def test_valid_upload_is_stored(self):
        self.draft_for(self.alice)
        self.upload(self.alice, pdf_file())
        self.assertEqual(ApplicationDocument.objects.count(), 1)

    def test_bad_type_and_oversize_are_rejected(self):
        self.draft_for(self.alice)
        self.upload(self.alice, SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream"))
        self.upload(self.alice, SimpleUploadedFile("big.pdf", b"x" * (5 * 1024 * 1024 + 1), content_type="application/pdf"))
        self.assertEqual(ApplicationDocument.objects.count(), 0)

    def test_no_upload_after_submission(self):
        self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        self.upload(self.alice, pdf_file())
        self.assertEqual(ApplicationDocument.objects.count(), 0)

    def test_only_owner_and_office_admin_can_download(self):
        self.draft_for(self.alice)
        self.upload(self.alice, pdf_file())
        doc = ApplicationDocument.objects.get()
        url = reverse("document_download", args=[doc.pk])
        for user, code in ((self.alice, 200), (self.boss, 200), (self.bob, 404)):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, code)
                if code == 200:
                    resp.close()
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_stored_filename_is_random_not_original(self):
        self.draft_for(self.alice)
        self.upload(self.alice, pdf_file(name="my-id-card.pdf"))
        self.assertNotIn("my-id-card", ApplicationDocument.objects.get().file.name)


class ReviewAndDecisionTests(AdmissionsBase):
    def test_review_pages_are_admin_only(self):
        app = self.draft_for(self.alice)
        for url in (reverse("review_list"), reverse("review_detail", args=[app.pk])):
            self.client.force_login(self.bob)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_login(self.alice)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_login(self.boss)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_applicant_cannot_post_a_decision(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "approved", "approved_programme": "Free place"})
        app.refresh_from_db()
        self.assertNotEqual(app.status, Application.Status.APPROVED)

    def test_approval_needs_a_programme(self):
        app = self.draft_for(self.alice)
        self.client.force_login(self.boss)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "approved", "approved_programme": ""})
        app.refresh_from_db()
        self.assertNotEqual(app.status, Application.Status.APPROVED)

    def test_more_info_needs_a_note(self):
        app = self.draft_for(self.alice)
        self.client.force_login(self.boss)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "more_info", "note": ""})
        app.refresh_from_db()
        self.assertNotEqual(app.status, Application.Status.INFO)

    def test_approval_creates_student_and_enables_letter(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        letter = reverse("letter_pdf", args=[app.pk])
        self.assertEqual(self.client.get(letter).status_code, 404)  # not approved yet
        self.client.force_login(self.boss)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "approved", "approved_programme": "Cambridge A Level Psychology 9990", "note": "Welcome"})
        app.refresh_from_db()
        self.alice.refresh_from_db()
        self.assertEqual(app.status, Application.Status.APPROVED)
        self.assertEqual(self.alice.role, User.Role.STUDENT)
        self.assertTrue(self.alice.student_id.startswith("PE-S-"))
        for user, code in ((self.alice, 200), (self.boss, 200), (self.bob, 404)):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                resp = self.client.get(letter)
                self.assertEqual(resp.status_code, code)
                if code == 200:
                    self.assertEqual(resp["Content-Type"], "application/pdf")
                    self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_decision_notifies_applicant_and_logs_history(self):
        app = self.draft_for(self.alice)
        self.client.post(reverse("application_submit"))
        mail.outbox.clear()
        self.client.force_login(self.boss)
        self.client.post(reverse("review_detail", args=[app.pk]), {"action": "declined", "note": "No places left"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(StatusHistory.objects.filter(application=app, new_status="declined", changed_by=self.boss).exists())
