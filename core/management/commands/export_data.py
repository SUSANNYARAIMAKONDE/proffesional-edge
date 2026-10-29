import csv
import os
from datetime import datetime

from django.apps import apps
from django.core.management.base import BaseCommand

# Passwords, uploaded files and students' written answers are deliberately NOT exported.
SPECS = {
    "users": ("accounts.User", ["id", "username", "email", "first_name", "last_name", "phone", "country", "role", "student_id", "is_active", "date_joined"]),
    "applications": ("admissions.Application", ["id", "reference", "user_id", "status", "full_name", "date_of_birth", "level", "subjects", "exam_board", "learning_mode", "submitted_at", "decided_at", "approved_programme"]),
    "courses": ("learning.Course", ["id", "title", "exam_board", "level", "subject", "tutor_id", "active"]),
    "enrolments": ("learning.Enrolment", ["id", "student_id", "course_id", "active", "created"]),
    "assignments": ("learning.Assignment", ["id", "course_id", "title", "due_date", "max_marks", "published"]),
    "submissions": ("learning.Submission", ["id", "assignment_id", "student_id", "submitted_at", "marks", "feedback", "released"]),
    "lessons": ("academics.Lesson", ["id", "course_id", "title", "start", "duration_minutes", "mode", "status"]),
    "attendance": ("academics.Attendance", ["id", "lesson_id", "student_id", "status"]),
    "quizzes": ("academics.Quiz", ["id", "course_id", "title", "open_at", "close_at", "published", "results_released"]),
    "quiz_attempts": ("academics.QuizAttempt", ["id", "quiz_id", "student_id", "score", "submitted_at"]),
    "parent_links": ("academics.ParentLink", ["id", "parent_id", "student_id", "verified", "created"]),
    "invoices": ("finance.Invoice", ["id", "student_id", "course_id", "description", "amount", "due_date", "cancelled", "created"]),
    "payments": ("finance.Payment", ["id", "invoice_id", "amount", "method", "reference", "received_on", "status", "receipt_number", "created"]),
}


class Command(BaseCommand):
    help = "Export users, applications, courses, enrolments, results, attendance and fees to CSV files (blueprint: data export)."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="", help="Output folder (default: exports/<timestamp>)")

    def handle(self, *args, **opts):
        out = opts["out"] or os.path.join("exports", datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(out, mode=0o700, exist_ok=True)
        for name, (label, fields) in SPECS.items():
            model = apps.get_model(label)
            path = os.path.join(out, f"{name}.csv")
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(fields)
                for obj in model._default_manager.all().iterator():
                    w.writerow([getattr(obj, f) for f in fields])
            os.chmod(path, 0o600)
        self.stdout.write(self.style.SUCCESS(f"Exported {len(SPECS)} files to {out}"))
        self.stdout.write("These files contain personal data. Store them securely and delete them when no longer needed.")
