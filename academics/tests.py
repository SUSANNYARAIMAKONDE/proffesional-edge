from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.testing import TempPrivateStorageMixin, make_user
from learning.models import Assignment, Course, Enrolment, Module, Resource, Submission
from .models import Attendance, Lesson, ParentLink, Question, Quiz, QuizAttempt
from .reports import build_report


class AcademicsBase(TempPrivateStorageMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.tutor = make_user("tutor1", User.Role.TUTOR)
        self.tutor2 = make_user("tutor2", User.Role.TUTOR)
        self.s1 = make_user("stud1", User.Role.STUDENT)
        self.s2 = make_user("stud2", User.Role.STUDENT)
        self.parent = make_user("parent1", User.Role.PARENT)
        self.parent2 = make_user("parent2", User.Role.PARENT)
        self.boss = make_user("boss", User.Role.ADMIN)
        self.course = Course.objects.create(title="Psychology A Level", tutor=self.tutor)
        self.course2 = Course.objects.create(title="History Course", tutor=self.tutor2)
        Enrolment.objects.create(student=self.s1, course=self.course)
        Enrolment.objects.create(student=self.s2, course=self.course2)
        ParentLink.objects.create(parent=self.parent, student=self.s1, verified=True)

    def code(self, user, url):
        self.client.logout()
        if user:
            self.client.force_login(user)
        return self.client.get(url).status_code


class StudentDataAccessTests(AcademicsBase):
    def test_report_access_matrix(self):
        url = reverse("report", args=[self.s1.pk])
        pdf = reverse("report_pdf", args=[self.s1.pk])
        for user, code in ((self.s1, 200), (self.parent, 200), (self.tutor, 200), (self.boss, 200),
                           (self.s2, 404), (self.parent2, 404), (self.tutor2, 404), (None, 302)):
            for u in (url, pdf):
                with self.subTest(user=getattr(user, "username", "anonymous"), url=u):
                    self.assertEqual(self.code(user, u), code)

    def test_unverified_parent_link_gives_no_access(self):
        ParentLink.objects.create(parent=self.parent2, student=self.s1, verified=False)
        for name in ("child_view", "report", "child_timetable"):
            with self.subTest(page=name):
                self.assertEqual(self.code(self.parent2, reverse(name, args=[self.s1.pk])), 404)

    def test_parent_dashboard_lists_only_verified_children(self):
        ParentLink.objects.create(parent=self.parent, student=self.s2, verified=False)
        self.client.force_login(self.parent)
        resp = self.client.get(reverse("parent_dashboard"))
        self.assertContains(resp, self.s1.first_name)
        self.assertNotContains(resp, self.s2.first_name)

    def test_child_view_only_for_verified_parent_of_that_child(self):
        self.assertEqual(self.code(self.parent, reverse("child_view", args=[self.s1.pk])), 200)
        self.assertEqual(self.code(self.parent, reverse("child_view", args=[self.s2.pk])), 404)
        self.assertEqual(self.code(self.s1, reverse("child_view", args=[self.s1.pk])), 404)  # students use own pages


class ReportReleaseTests(AcademicsBase):
    def test_unreleased_results_never_appear_in_report(self):
        a = Assignment.objects.create(course=self.course, title="A1", instructions="x",
                                      due_date=timezone.now() + timedelta(days=1), max_marks=100, published=True)
        sub = Submission.objects.create(assignment=a, student=self.s1, text="x", marks=Decimal("77"), feedback="fb", released=False)
        quiz = Quiz.objects.create(course=self.course, title="Q1", open_at=timezone.now() - timedelta(hours=2),
                                   close_at=timezone.now() - timedelta(hours=1), published=True, results_released=False)
        Question.objects.create(quiz=quiz, text="?", option_a="a", option_b="b", correct="a", marks=2)
        QuizAttempt.objects.create(quiz=quiz, student=self.s1, score=2)
        row = build_report(self.s1)[0]
        self.assertEqual(row["assignments"], [])
        self.assertEqual(row["quizzes"], [])
        sub.released = True
        sub.save()
        quiz.results_released = True
        quiz.save()
        row = build_report(self.s1)[0]
        self.assertEqual(row["assignments"][0][1], Decimal("77"))
        self.assertEqual(row["quizzes"][0][1:], (2, 2))

    def test_attendance_counts_present_and_late_only(self):
        for i, st in enumerate(("present", "late", "absent", "excused")):
            lesson = Lesson.objects.create(course=self.course, title=f"L{i}", start=timezone.now() - timedelta(days=i + 1), status="held")
            Attendance.objects.create(lesson=lesson, student=self.s1, status=st)
        row = build_report(self.s1)[0]
        self.assertEqual((row["attended"], row["held"], row["attendance_pct"]), (2, 4, 50))


class QuizTests(AcademicsBase):
    def make_quiz(self, **kw):
        defaults = dict(course=self.course, title="Practice Quiz", open_at=timezone.now() - timedelta(hours=1),
                        close_at=timezone.now() + timedelta(hours=1), published=True)
        defaults.update(kw)
        quiz = Quiz.objects.create(**defaults)
        self.q1 = Question.objects.create(quiz=quiz, text="Q1?", option_a="right", option_b="wrong", correct="a", marks=2)
        self.q2 = Question.objects.create(quiz=quiz, text="Q2?", option_a="wrong", option_b="right", correct="b", marks=3)
        return quiz

    def test_auto_marking_and_single_attempt(self):
        quiz = self.make_quiz()
        self.client.force_login(self.s1)
        url = reverse("quiz_detail", args=[quiz.pk])
        self.client.post(url, {f"q{self.q1.id}": "a", f"q{self.q2.id}": "a"})
        self.assertEqual(QuizAttempt.objects.get().score, 2)
        self.client.post(url, {f"q{self.q1.id}": "a", f"q{self.q2.id}": "b"})
        self.assertEqual(QuizAttempt.objects.count(), 1)
        self.assertEqual(QuizAttempt.objects.get().score, 2)

    def test_closed_or_unopened_quiz_rejects_answers(self):
        closed = self.make_quiz(close_at=timezone.now() - timedelta(minutes=1))
        self.client.force_login(self.s1)
        self.client.post(reverse("quiz_detail", args=[closed.pk]), {f"q{self.q1.id}": "a"})
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_score_hidden_until_released(self):
        quiz = self.make_quiz()
        QuizAttempt.objects.create(quiz=quiz, student=self.s1, score=5)
        self.client.force_login(self.s1)
        url = reverse("quiz_detail", args=[quiz.pk])
        self.assertNotContains(self.client.get(url), "Score:")
        quiz.results_released = True
        quiz.save()
        self.assertContains(self.client.get(url), "Score:")

    def test_only_enrolled_students_can_open_quiz(self):
        quiz = self.make_quiz()
        url = reverse("quiz_detail", args=[quiz.pk])
        for user, code in ((self.s1, 200), (self.s2, 404), (self.parent, 404), (self.tutor, 404), (None, 302)):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.assertEqual(self.code(user, url), code)

    def test_unpublished_quiz_is_hidden(self):
        quiz = self.make_quiz(published=False)
        self.assertEqual(self.code(self.s1, reverse("quiz_detail", args=[quiz.pk])), 404)


class LessonAndAttendanceTests(AcademicsBase):
    def setUp(self):
        super().setUp()
        self.lesson = Lesson.objects.create(course=self.course, title="Algebra Intro", start=timezone.now() + timedelta(days=1))
        self.other_lesson = Lesson.objects.create(course=self.course2, title="Other Course Lesson", start=timezone.now() + timedelta(days=1))

    def test_timetable_shows_only_own_courses(self):
        self.client.force_login(self.s1)
        resp = self.client.get(reverse("timetable"))
        self.assertContains(resp, "Algebra Intro")
        self.assertNotContains(resp, "Other Course Lesson")

    def test_child_timetable_access(self):
        url = reverse("child_timetable", args=[self.s1.pk])
        for user, code in ((self.parent, 200), (self.s2, 404), (self.parent2, 404)):
            with self.subTest(user=user.username):
                self.assertEqual(self.code(user, url), code)

    def test_tutor_records_attendance_and_lesson_becomes_held(self):
        self.client.force_login(self.tutor)
        self.client.post(reverse("attendance_register", args=[self.lesson.pk]), {f"s{self.s1.id}": "late"})
        self.assertEqual(Attendance.objects.get().status, "late")
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, "held")

    def test_invalid_attendance_value_ignored(self):
        self.client.force_login(self.tutor)
        self.client.post(reverse("attendance_register", args=[self.lesson.pk]), {f"s{self.s1.id}": "hacked"})
        self.assertEqual(Attendance.objects.count(), 0)

    def test_attendance_and_lesson_pages_restricted_to_course_tutor(self):
        for name, arg in (("attendance_register", self.lesson.pk), ("tutor_lessons", self.course.pk)):
            url = reverse(name, args=[arg])
            for user, code in ((self.tutor, 200), (self.boss, 200), (self.tutor2, 404), (self.s1, 404), (self.parent, 404)):
                with self.subTest(page=name, user=user.username):
                    self.assertEqual(self.code(user, url), code)
        self.client.force_login(self.s1)
        self.client.post(reverse("attendance_register", args=[self.lesson.pk]), {f"s{self.s1.id}": "present"})
        self.assertEqual(Attendance.objects.count(), 0)


class TutorSelfServiceTests(AcademicsBase):
    def setUp(self):
        super().setUp()
        self.module = Module.objects.create(course=self.course, title="Unit 1")
        self.other_module = Module.objects.create(course=self.course2, title="Other unit")

    def post_resource(self, user, course, **kw):
        data = dict(module=self.module.pk, title="Notes", description="", link="https://example.com/video",
                    access_level="enrolled", published="on")
        data.update(kw)
        self.client.force_login(user)
        self.client.post(reverse("tutor_resource_add", args=[course.pk]), data)

    def test_tutor_can_add_resource_to_own_course(self):
        self.post_resource(self.tutor, self.course)
        r = Resource.objects.get()
        self.assertEqual(r.uploaded_by, self.tutor)

    def test_tutor_cannot_use_another_courses_module(self):
        self.post_resource(self.tutor, self.course, module=self.other_module.pk)
        self.assertEqual(Resource.objects.count(), 0)

    def test_tutor_cannot_publish_publicly(self):
        self.post_resource(self.tutor, self.course, access_level="public")
        self.assertEqual(Resource.objects.count(), 0)

    def test_tutor_cannot_touch_another_tutors_course(self):
        self.post_resource(self.tutor2, self.course)
        self.assertEqual(Resource.objects.count(), 0)
        self.assertEqual(self.code(self.tutor2, reverse("tutor_resource_add", args=[self.course.pk])), 404)
        self.assertEqual(self.code(self.tutor2, reverse("tutor_assignment_add", args=[self.course.pk])), 404)

    def test_resource_needs_file_or_link(self):
        self.post_resource(self.tutor, self.course, link="")
        self.assertEqual(Resource.objects.count(), 0)

    def test_student_cannot_create_assignments(self):
        self.client.force_login(self.s1)
        resp = self.client.post(reverse("tutor_assignment_add", args=[self.course.pk]),
                                {"title": "Free marks", "instructions": "x", "due_date": "2030-01-01T10:00", "max_marks": 1})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(Assignment.objects.count(), 0)

    def test_tutor_creates_assignment(self):
        self.client.force_login(self.tutor)
        self.client.post(reverse("tutor_assignment_add", args=[self.course.pk]),
                         {"title": "Essay", "instructions": "Write", "due_date": "2030-01-01T10:00", "max_marks": 50, "published": "on"})
        a = Assignment.objects.get()
        self.assertEqual((a.course, a.max_marks), (self.course, 50))
