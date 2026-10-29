from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0b1f4a")


def build_receipt(p):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A5, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title=f"Receipt {p.receipt_number}")
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], textColor=NAVY, alignment=0, fontSize=18)
    inv = p.invoice
    rows = [["Receipt no.", p.receipt_number], ["Date received", p.received_on.strftime("%d %B %Y")],
            ["Received from", inv.student.get_full_name()], ["Student ID", inv.student.student_id or "-"],
            ["For", f"{inv.number} - {inv.description}"], ["Method", p.get_method_display()],
            ["Reference", p.reference or "-"], ["Amount paid", f"USD {p.amount:,.2f}"],
            ["Invoice balance after payment", f"USD {inv.balance:,.2f}"]]
    t = Table(rows, colWidths=[48 * mm, 70 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    doc.build([Paragraph("PROFESSIONAL EDGE", h), Paragraph("Official Payment Receipt", ss["Heading3"]), Spacer(1, 4 * mm), t,
               Spacer(1, 8 * mm), Paragraph("Thank you. Queries: +263 784 189 241 / ppmapuranga95@gmail.com", ss["Italic"])])
    return buf.getvalue()
