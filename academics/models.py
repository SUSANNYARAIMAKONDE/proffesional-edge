from django.conf import settings
from django.db import models

from learning.models import Course


class Lesson(models.Model):
    class Mode(models.TextChoices):
        ONLINE = "online", "Online"
        INPERSON = "in_person", "In person / home visit"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        HELD = "held", "Held"
        CANCELLED = "cancelled", "Cancelled"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=160)
    start = models.DateTimeField(help_text="Africa/Harare time")
    duration_minutes = models.PositiveIntegerField(default=60)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    location = models.CharField(max_length=300, blank=True, help_text="Address, or the Zoom/Google Meet link")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.course}: {self.title}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        LATE = "late", "Late"
        ABSENT = "absent", "Absent"
        EXCUSED = "excused", "Excused"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)

    class Meta:
        unique_together = ("lesson", "student")


class ParentLink(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="children_links")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="parent_links")
    verified = models.BooleanField(default=False, help_text="Tick only after verifying the relationship and consent")
    note = models.CharField(max_length=200, blank=True, help_text="How/when this link was verified")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("parent", "student")

    def __str__(self):
        return f"{self.parent} -> {self.student}"


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=160)
    instructions = models.TextField(blank=True)
    open_at = models.DateTimeField()
    close_at = models.DateTimeField()
    published = models.BooleanField(default=False)
    results_released = models.BooleanField(default=False, help_text="Students/parents see scores only when ticked")

    class Meta:
        ordering = ["open_at"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return f"{self.course}: {self.title} (practice quiz)"

    @property
    def total_marks(self):
        return sum(q.marks for q in self.questions.all())


class Question(models.Model):
    CHOICES = [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300, blank=True)
    option_d = models.CharField(max_length=300, blank=True)
    correct = models.CharField(max_length=1, choices=CHOICES)
    marks = models.PositiveIntegerField(default=1)

    @property
    def options(self):
        pairs = [("a", self.option_a), ("b", self.option_b), ("c", self.option_c), ("d", self.option_d)]
        return [(k, v) for k, v in pairs if v]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    answers = models.JSONField(default=dict)
    score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("quiz", "student")
