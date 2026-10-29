from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.testing import TempPrivateStorageMixin, make_user, pdf_file
from .models import Assignment, Course, Enrolment, Module, Resource, Submission


class LearningBase(TempPrivateStorageMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.tutor = make_user("tutor1", User.Role.TUTOR)
        self.tutor2 = make_user("tutor2", User.Role.TUTOR)
        self.s1 = make_user("stud1", User.Role.STUDENT)   # enrolled
        self.s2 = make_user("stud2", User.Role.STUDENT)   # not enrolled
        self.boss = make_user("boss", User.Role.ADMIN)
        self.course = Course.objects.create(title="IGCSE English", tutor=self.tutor)
        Enrolment.objects.create(student=self.s1, course=self.course)
        self.module = Module.objects.create(course=self.course, title="Unit 1")
        self.assignment = Assignment.objects.create(course=self.course, title="Essay 1", instructions="Write",
                                                    due_date=timezone.now() + timedelta(days=3), max_marks=100, published=True)

    def res(self, title, level, published=True):
        return Resource.objects.create(module=self.module, title=title, file=pdf_file(), access_level=level, published=published)

    def status(self, user, url):
        self.client.logout()
        if user:
            self.client.force_login(user)
        resp = self.client.get(url)
        if resp.status_code == 200 and getattr(resp, "streaming", False):
            resp.close()
        return resp.status_code


class CourseAccessTests(LearningBase):
    def test_course_page_access_matrix(self):
        url = reverse("course_detail", args=[self.course.pk])
        for user, code in ((self.s1, 200), (self.tutor, 200), (self.boss, 200), (self.s2, 404), (self.tutor2, 404), (None, 302)):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.assertEqual(self.status(user, url), code)

    def test_inactive_enrolment_loses_access(self):
        Enrolment.objects.filter(student=self.s1).update(active=False)
        self.assertEqual(self.status(self.s1, reverse("course_detail", args=[self.course.pk])), 404)

    def test_student_dashboard_lists_only_own_courses(self):
        other = Course.objects.create(title="Secret Other Course", tutor=self.tutor2)
        Enrolment.objects.create(student=self.s2, course=other)
        self.client.force_login(self.s1)
        resp = self.client.get(reverse("student_dashboard"))
        self.assertContains(resp, "IGCSE English")
        self.assertNotContains(resp, "Secret Other Course")


class ResourceAccessTests(LearningBase):
    def test_access_levels(self):
        pub, reg = self.res("Public", "public"), self.res("Registered", "registered")
        enr, tut = self.res("Enrolled", "enrolled"), self.res("TutorOnly", "tutor")
        matrix = {
            pub: {None: 200, self.s2: 200, self.s1: 200},
            reg: {None: 404, self.s2: 200, self.s1: 200},
            enr: {None: 404, self.s2: 404, self.s1: 200, self.tutor: 200, self.tutor2: 404, self.boss: 200},
            tut: {None: 404, self.s1: 404, self.s2: 404, self.tutor: 200, self.tutor2: 404, self.boss: 200},
        }
        for r, cases in matrix.items():
            for user, code in cases.items():
                with self.subTest(resource=r.title, user=getattr(user, "username", "anonymous")):
                    self.assertEqual(self.status(user, reverse("resource_download", args=[r.pk])), code)

    def test_unpublished_resource_is_staff_only(self):
        r = self.res("Draft", "enrolled", published=False)
        url = reverse("resource_download", args=[r.pk])
        self.assertEqual(self.status(self.s1, url), 404)
        self.assertEqual(self.status(self.tutor, url), 200)
        self.assertEqual(self.status(self.tutor2, url), 404)

    def test_course_page_hides_resources_student_cannot_open(self):
        self.res("Visible Notes", "enrolled")
        self.res("Marking Guide", "tutor")
        self.client.force_login(self.s1)
        resp = self.client.get(reverse("course_detail", args=[self.course.pk]))
        self.assertContains(resp, "Visible Notes")
        self.assertNotContains(resp, "Marking Guide")


class AssignmentTests(LearningBase):
    def url(self):
        return reverse("assignment_detail", args=[self.assignment.pk])

    def test_enrolled_student_can_submit_and_resubmit(self):
        self.client.force_login(self.s1)
        self.client.post(self.url(), {"text": "First"})
        self.client.post(self.url(), {"text": "Second"})
        self.assertEqual(Submission.objects.filter(student=self.s1).count(), 1)
        self.assertEqual(Submission.objects.get(student=self.s1).text, "Second")

    def test_non_enrolled_student_is_blocked(self):
        self.client.force_login(self.s2)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.post(self.url(), {"text": "sneaky"})
        self.assertEqual(Submission.objects.count(), 0)

    def test_empty_submission_rejected(self):
        self.client.force_login(self.s1)
        self.client.post(self.url(), {"text": ""})
        self.assertEqual(Submission.objects.count(), 0)

    def test_overdue_submission_rejected(self):
        self.assignment.due_date = timezone.now() - timedelta(days=1)
        self.assignment.save()
        self.client.force_login(self.s1)
        self.client.post(self.url(), {"text": "late"})
        self.assertEqual(Submission.objects.count(), 0)

    def test_unpublished_assignment_is_hidden(self):
        self.assignment.published = False
        self.assignment.save()
        self.client.force_login(self.s1)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_marks_and_feedback_hidden_until_released(self):
        sub = Submission.objects.create(assignment=self.assignment, student=self.s1, text="x", marks=73, feedback="SECRETFEEDBACK")
        self.client.force_login(self.s1)
        self.assertNotContains(self.client.get(self.url()), "SECRETFEEDBACK")
        sub.released = True
        sub.save()
        self.assertContains(self.client.get(self.url()), "SECRETFEEDBACK")

    def test_returned_work_is_locked(self):
        Submission.objects.create(assignment=self.assignment, student=self.s1, text="original", marks=60, released=True)
        self.client.force_login(self.s1)
        self.client.post(self.url(), {"text": "changed after marking"})
        self.assertEqual(Submission.objects.get().text, "original")

    def test_submission_files_are_private(self):
        sub = Submission.objects.create(assignment=self.assignment, student=self.s1, file=pdf_file("work.pdf"))
        url = reverse("submission_file", args=[sub.pk])
        for user, code in ((self.s1, 200), (self.tutor, 200), (self.boss, 200), (self.s2, 404), (self.tutor2, 404), (None, 302)):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.assertEqual(self.status(user, url), code)


class TutorToolsTests(LearningBase):
    def setUp(self):
        super().setUp()
        self.sub = Submission.objects.create(assignment=self.assignment, student=self.s1, text="answer")

    def test_tutor_pages_access(self):
        for name, args in (("tutor_course", [self.course.pk]), ("mark_submission", [self.sub.pk])):
            url = reverse(name, args=args)
            for user, code in ((self.tutor, 200), (self.boss, 200), (self.tutor2, 404), (self.s1, 404), (self.s2, 404)):
                with self.subTest(page=name, user=user.username):
                    self.assertEqual(self.status(user, url), code)

    def test_other_tutor_cannot_mark(self):
        self.client.force_login(self.tutor2)
        self.client.post(reverse("mark_submission", args=[self.sub.pk]), {"marks": "90", "feedback": "x", "released": "on"})
        self.sub.refresh_from_db()
        self.assertIsNone(self.sub.marks)

    def test_marks_above_maximum_rejected(self):
        self.client.force_login(self.tutor)
        self.client.post(reverse("mark_submission", args=[self.sub.pk]), {"marks": "150", "feedback": "x"})
        self.sub.refresh_from_db()
        self.assertIsNone(self.sub.marks)

    def test_tutor_marks_and_releases(self):
        self.client.force_login(self.tutor)
        self.client.post(reverse("mark_submission", args=[self.sub.pk]), {"marks": "82", "feedback": "Well done", "released": "on"})
        self.sub.refresh_from_db()
        self.assertEqual(int(self.sub.marks), 82)
        self.assertTrue(self.sub.released)
        self.assertEqual(self.sub.marked_by, self.tutor)

    def test_tutor_dashboard_shows_only_own_courses(self):
        Course.objects.create(title="Other Tutor Course", tutor=self.tutor2)
        self.client.force_login(self.tutor)
        resp = self.client.get(reverse("tutor_dashboard"))
        self.assertContains(resp, "IGCSE English")
        self.assertNotContains(resp, "Other Tutor Course")
