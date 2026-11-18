from typing import Any, List
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    and persistent running footers on every page.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[dict] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()  # type: ignore[attr-defined]

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.75)
        # Running horizontal rule above footer
        self.line(36, 28, 595.27 - 36, 28)
        self.drawString(36, 17, "TMA V2 — Monthly Trekking Activity & Performance Audit Report")
        page_num = getattr(self, '_pageNumber', 1)
        self.drawRightString(
            595.27 - 36,
            17,
            f"Page {page_num} of {page_count}  |  IITM BS Degree MAD 2"
        )
        self.restoreState()


def generate_monthly_pdf(
    pdf_path: str,
    year: int,
    month: int,
    metrics: dict,
    top_treks: list,
    recent_bookings: list
) -> str:
    """
    Generates a pixel-perfect, professionally formatted PDF monthly activity report.
    """
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=2
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=6,
        spaceAfter=4
    )

    # Crisp White Table Header Styles
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0
    )

    header_cell_center = ParagraphStyle(
        'HeaderCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    # Body Cell Styles
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )

    cell_style_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
        alignment=1
    )

    cell_sub_style = ParagraphStyle(
        'TableCellSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor('#64748b')
    )

    # Printable area: 595.27 - 72 = 523.27pt width
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=30,
        bottomMargin=38
    )

    story = []

    # 1. Header & Title Block
    story.append(Paragraph("TMA V2 — Monthly Trekking Activity & Analytics Report", title_style))
    gen_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    month_name = datetime(year, month, 1).strftime('%B %Y')
    story.append(Paragraph(
        f"<b>Report Period:</b> {month_name} ({year}-{month:02d}) &nbsp;|&nbsp; "
        f"<b>Generated:</b> {gen_time} UTC &nbsp;|&nbsp; "
        f"<b>System:</b> Administrator Portal",
        meta_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

    # 2. Executive KPI Cards
    total_treks = metrics.get('total_treks', 0)
    open_treks = metrics.get('open_treks', 0)
    total_users = metrics.get('total_users', 0)
    total_staff = metrics.get('total_staff', 0)
    confirmed_bookings = metrics.get('confirmed_bookings', 0)
    cancelled_bookings = metrics.get('cancelled_bookings', 0)
    total_bookings = metrics.get('total_bookings', 0)

    success_rate = f"{(confirmed_bookings / total_bookings * 100):.1f}%" if total_bookings > 0 else "N/A"

    kpi_title_style = ParagraphStyle('KPITitle', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.HexColor('#64748b'), alignment=1)
    kpi_val_style = ParagraphStyle('KPIVal', fontName='Helvetica-Bold', fontSize=17, leading=20, textColor=colors.HexColor('#0284c7'), alignment=1)
    kpi_val_green = ParagraphStyle('KPIValG', fontName='Helvetica-Bold', fontSize=17, leading=20, textColor=colors.HexColor('#10b981'), alignment=1)
    kpi_sub_style = ParagraphStyle('KPISub', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#94a3b8'), alignment=1)

    metric_data = [
        [
            [
                Paragraph("TOTAL EXPEDITIONS", kpi_title_style),
                Paragraph(str(total_treks), kpi_val_style),
                Paragraph(f"{open_treks} Currently Open", kpi_sub_style)
            ],
            [
                Paragraph("TREKKERS & STAFF", kpi_title_style),
                Paragraph(str(total_users), kpi_val_style),
                Paragraph(f"{total_staff} Staff Members", kpi_sub_style)
            ],
            [
                Paragraph("CONFIRMED BOOKINGS", kpi_title_style),
                Paragraph(str(confirmed_bookings), kpi_val_style),
                Paragraph(f"{cancelled_bookings} Cancelled", kpi_sub_style)
            ],
            [
                Paragraph("FULFILLMENT RATE", kpi_title_style),
                Paragraph(success_rate, kpi_val_green),
                Paragraph("Booking Conversion", kpi_sub_style)
            ],
        ]
    ]

    t_metric = Table(metric_data, colWidths=[130.75, 130.75, 130.75, 130.75])
    t_metric.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_metric)
    story.append(Spacer(1, 10))

    # 3. Top Performing Trek Routes
    story.append(Paragraph("Top Performing Trek Routes by Registration Volume", h2_style))
    treks_table_data: List[List[Any]] = [
        [
            Paragraph("<b>#</b>", header_cell_center),
            Paragraph("<b>Trek Route Name</b>", header_cell),
            Paragraph("<b>Location</b>", header_cell),
            Paragraph("<b>Difficulty</b>", header_cell_center),
            Paragraph("<b>Confirmed Trekkers</b>", header_cell_center),
        ]
    ]

    diff_color_map = {
        'Easy': '#16a34a',
        'Moderate': '#d97706',
        'Hard': '#dc2626'
    }

    for idx, t in enumerate(top_treks, start=1):
        diff = t.get('difficulty', 'Moderate')
        diff_col = diff_color_map.get(diff, '#0284c7')
        treks_table_data.append([
            Paragraph(f"<b>{idx}</b>", cell_style_center),
            Paragraph(f"<b>{t.get('name', 'N/A')}</b>", cell_style),
            Paragraph(t.get('location', 'N/A'), cell_style),
            Paragraph(f"<font color='{diff_col}'><b>{diff}</b></font>", cell_style_center),
            Paragraph(f"<font color='#0284c7'><b>{t.get('bookings', 0)} confirmed</b></font>", cell_style_center),
        ])

    if len(treks_table_data) == 1:
        treks_table_data.append([
            Paragraph("-", cell_style_center),
            Paragraph("No treks recorded for this period", cell_style),
            Paragraph("-", cell_style),
            Paragraph("-", cell_style_center),
            Paragraph("-", cell_style_center),
        ])

    t_treks = Table(treks_table_data, colWidths=[26, 186, 150, 75, 86])
    t_treks.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_treks)
    story.append(Spacer(1, 10))

    # 4. Recent Reservations & Booking Audit Log
    story.append(Paragraph("Recent Reservations & Booking Audit Log", h2_style))
    booking_table_data: List[List[Any]] = [
        [
            Paragraph("<b>ID</b>", header_cell_center),
            Paragraph("<b>Trekker Name & Contact</b>", header_cell),
            Paragraph("<b>Trek Route Destination</b>", header_cell),
            Paragraph("<b>Seats</b>", header_cell_center),
            Paragraph("<b>Date Reserved</b>", header_cell_center),
            Paragraph("<b>Status</b>", header_cell_center),
        ]
    ]

    # Show up to 10 recent bookings on summary report
    for b in recent_bookings[:10]:
        status_val = str(b.get('status', 'Confirmed')).upper()
        if status_val == 'CONFIRMED':
            status_color = '#059669'
        elif status_val == 'CANCELLED':
            status_color = '#dc2626'
        else:
            status_color = '#2563eb'

        # Clean date display (extract YYYY-MM-DD)
        raw_date = str(b.get('booking_date', ''))
        clean_date = raw_date.split('T')[0].split(' ')[0] if raw_date else 'N/A'

        booking_table_data.append([
            Paragraph(f"<b>#{b.get('id', '')}</b>", cell_style_center),
            [
                Paragraph(f"<b>{b.get('user_name', '')}</b>", cell_style),
                Paragraph(b.get('user_email', ''), cell_sub_style)
            ],
            Paragraph(b.get('trek_name', ''), cell_style),
            Paragraph(str(b.get('seats_booked', 1)), cell_style_center),
            Paragraph(clean_date, cell_style_center),
            Paragraph(f"<font color='{status_color}'><b>{status_val}</b></font>", cell_style_center),
        ])

    if len(booking_table_data) == 1:
        booking_table_data.append([
            Paragraph("-", cell_style_center),
            Paragraph("No reservations found", cell_style),
            Paragraph("-", cell_style),
            Paragraph("-", cell_style_center),
            Paragraph("-", cell_style_center),
            Paragraph("-", cell_style_center),
        ])

    t_bookings = Table(booking_table_data, colWidths=[32, 150, 155, 38, 72, 76], repeatRows=1)
    t_bookings.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_bookings)

    doc.build(story, canvasmaker=NumberedCanvas)
    return pdf_path
