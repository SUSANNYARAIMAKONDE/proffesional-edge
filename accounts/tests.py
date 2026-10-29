from django.core import mail, signing
from django.test import TestCase
from django.urls import reverse

from .models import User
from .testing import PASSWORD, make_user
from .views import SALT


class RegistrationTests(TestCase):
    payload = dict(full_name="Tendai Moyo", email="t@example.com", phone="+263771234567", country="Zimbabwe",
                   password1=PASSWORD, password2=PASSWORD, accept_terms="on")

    def test_register_creates_inactive_user_and_sends_verification(self):
        resp = self.client.post(reverse("register"), self.payload)
        self.assertEqual(resp.status_code, 200)
        user = User.objects.get(email="t@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, User.Role.APPLICANT)
        self.assertEqual(len(mail.outbox), 1)

    def test_verification_link_activates_account(self):
        self.client.post(reverse("register"), self.payload)
        user = User.objects.get(email="t@example.com")
        self.client.get(reverse("verify_email", args=[signing.dumps(user.pk, salt=SALT)]))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_bad_token_does_not_activate(self):
        self.client.post(reverse("register"), self.payload)
        resp = self.client.get(reverse("verify_email", args=["not-a-real-token"]))
        self.assertContains(resp, "invalid or expired")
        self.assertFalse(User.objects.get(email="t@example.com").is_active)

    def test_unverified_user_cannot_log_in(self):
        self.client.post(reverse("register"), self.payload)
        self.client.post(reverse("login"), {"username": "t@example.com", "password": PASSWORD})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_duplicate_email_rejected(self):
        make_user("existing")
        data = dict(self.payload, email="existing@example.com")
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.filter(email="existing@example.com").count(), 1)

    def test_weak_or_mismatched_password_rejected(self):
        self.client.post(reverse("register"), dict(self.payload, password1="12345", password2="12345"))
        self.client.post(reverse("register"), dict(self.payload, email="b@example.com", password2="Different-Pass-1!"))
        self.assertEqual(User.objects.count(), 0)

    def test_terms_must_be_accepted(self):
        data = dict(self.payload)
        data.pop("accept_terms")
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.count(), 0)


class DashboardRoutingTests(TestCase):
    def test_each_role_lands_on_its_own_dashboard(self):
        expected = {
            User.Role.APPLICANT: "my_application", User.Role.STUDENT: "student_dashboard",
            User.Role.TUTOR: "tutor_dashboard", User.Role.PARENT: "parent_dashboard",
            User.Role.FINANCE: "finance_dashboard", User.Role.ADMIN: "review_list",
        }
        for role, name in expected.items():
            with self.subTest(role=role):
                user = make_user(f"u_{role}", role)
                self.client.force_login(user)
                resp = self.client.get(reverse("dashboard"))
                self.assertRedirects(resp, reverse(name), fetch_redirect_response=False)

    def test_anonymous_is_sent_to_login(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])


class PasswordChangeTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse("password_change"))
        self.assertEqual(resp.status_code, 302)

    def test_user_can_change_password(self):
        user = make_user("changer")
        self.client.force_login(user)
        new = "An0ther-Strong-Pass!"
        resp = self.client.post(reverse("password_change"), {"old_password": PASSWORD, "new_password1": new, "new_password2": new})
        self.assertRedirects(resp, reverse("password_change_done"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new))

    def test_wrong_old_password_rejected(self):
        user = make_user("changer2")
        self.client.force_login(user)
        new = "An0ther-Strong-Pass!"
        self.client.post(reverse("password_change"), {"old_password": "wrong", "new_password1": new, "new_password2": new})
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))


class SetupGroupsTests(TestCase):
    def test_office_staff_group_can_manage_but_not_edit_audit_log(self):
        from io import StringIO
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        call_command("setup_groups", stdout=StringIO())
        codenames = set(Group.objects.get(name="Office Staff").permissions.values_list("codename", flat=True))
        self.assertIn("change_programme", codenames)
        self.assertIn("change_application", codenames)
        self.assertIn("view_auditentry", codenames)
        self.assertNotIn("delete_auditentry", codenames)
        self.assertNotIn("change_auditentry", codenames)
        self.assertNotIn("delete_user", codenames)
