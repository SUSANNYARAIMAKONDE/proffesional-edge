from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0b1f4a")
GOLD = colors.HexColor("#c9a24a")


def build_admission_letter(app):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm, title="Admission Letter")
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], textColor=NAVY, fontSize=22, alignment=0)
    tag = ParagraphStyle("tag", parent=ss["Normal"], textColor=GOLD, fontSize=10)
    body = ParagraphStyle("b", parent=ss["Normal"], fontSize=11, leading=16)
    date = (app.decided_at or timezone.now()).strftime("%d %B %Y")
    sid = app.user.student_id or "pending"
    rows = [["Student name", app.full_name], ["Student ID", sid], ["Reference", app.reference],
            ["Approved programme", app.approved_programme], ["Academic level", app.level],
            ["Examination board", app.get_exam_board_display()], ["Learning mode", app.get_learning_mode_display()],
            ["Date of admission", date]]
    t = Table(rows, colWidths=[55 * mm, 105 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story = [Paragraph("PROFESSIONAL EDGE", h), Paragraph("Bridging School and Home Learning", tag), Spacer(1, 12 * mm),
             Paragraph("ADMISSION LETTER", ParagraphStyle("t", parent=ss["Heading2"], textColor=NAVY)),
             Paragraph(f"Dear {app.full_name},", body), Spacer(1, 4 * mm),
             Paragraph("We are pleased to confirm that your application has been approved. Your admission details are below.", body),
             Spacer(1, 6 * mm), t, Spacer(1, 8 * mm),
             Paragraph("<b>Next steps:</b> log in to your Professional Edge account to view your timetable and learning "
                       "materials as they are made available, and contact us with any questions. "
                       "Fees, terms and conditions will be confirmed by Professional Edge in writing.", body),
             Spacer(1, 12 * mm), Paragraph("Professional Edge<br/>Call/WhatsApp: +263 784 189 241<br/>Email: ppmapuranga95@gmail.com", body)]
    doc.build(story)
    return buf.getvalue()
