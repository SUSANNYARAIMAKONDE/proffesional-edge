from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from learning.models import Course, Submission
from .models import Attendance, Lesson, QuizAttempt


def build_report(student):
    """Only RELEASED results are included, so parents and students never see unreleased marks."""
    out = []
    courses = Course.objects.filter(enrolments__student=student, enrolments__active=True).distinct()
    for c in courses:
        held = Lesson.objects.filter(course=c, status="held")
        attended = Attendance.objects.filter(student=student, lesson__in=held, status__in=["present", "late"]).count()
        n_held = held.count()
        subs = Submission.objects.filter(student=student, assignment__course=c, released=True, marks__isnull=False).select_related("assignment")
        attempts = QuizAttempt.objects.filter(student=student, quiz__course=c, quiz__results_released=True).select_related("quiz")
        out.append({
            "course": c, "held": n_held, "attended": attended,
            "attendance_pct": round(attended * 100 / n_held) if n_held else None,
            "assignments": [(s.assignment.title, s.marks, s.assignment.max_marks, s.feedback) for s in subs],
            "quizzes": [(a.quiz.title, a.score, a.quiz.total_marks) for a in attempts],
        })
    return out


def report_pdf(student, rows):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
                            title="Progress Report")
    ss = getSampleStyleSheet()
    story = [Paragraph("Professional Edge - Learner Progress Report", ss["Title"]),
             Paragraph(f"<b>{student.get_full_name()}</b> &nbsp; Student ID: {student.student_id or '-'}", ss["Normal"]),
             Paragraph("Practice quizzes and assignments are tutor assessments, not official examination results.", ss["Italic"]),
             Spacer(1, 6 * mm)]
    for r in rows:
        story.append(Paragraph(r["course"].title, ss["Heading2"]))
        att = f"{r['attended']} / {r['held']} lessons ({r['attendance_pct']}%)" if r["held"] else "No lessons recorded yet"
        data = [["Attendance", att]]
        data += [[f"Assignment: {t}", f"{m} / {mx}"] for t, m, mx, _ in r["assignments"]]
        data += [[f"Quiz: {t}", f"{s} / {tot}"] for t, s, tot in r["quizzes"]]
        tbl = Table(data, colWidths=[100 * mm, 70 * mm])
        tbl.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey)]))
        story += [tbl]
        for t, m, mx, fb in r["assignments"]:
            if fb:
                story.append(Paragraph(f"<b>Tutor comment ({t}):</b> {fb}", ss["Normal"]))
        story.append(Spacer(1, 5 * mm))
    if not rows:
        story.append(Paragraph("No enrolments yet.", ss["Normal"]))
    doc.build(story)
    return buf.getvalue()
