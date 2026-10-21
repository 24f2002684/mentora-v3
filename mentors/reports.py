import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from students.models import StudentProfile, Goal, LearningMilestone
from mentors.models import TaskSubmission, CompetencyAssessment


def generate_student_growth_pdf(student: StudentProfile, assessor_name="VRCF Lead Mentor") -> io.BytesIO:
    """
    Generates a professional, print-ready PDF Growth Report using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles with VRCF branding colors
    primary_color = colors.HexColor("#0d9488")
    dark_text = colors.HexColor("#0f172a")
    muted_text = colors.HexColor("#64748b")
    border_color = colors.HexColor("#e2e8f0")
    surface_bg = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=muted_text,
        spaceAfter=14
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=dark_text
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=body_bold,
        textColor=colors.HexColor("#0f766e"),
        fontSize=8.5,
        leading=11
    )

    elements = []

    # 1. Header with Foundation Branding
    header_data = [
        [
            Paragraph("<b>MENTORA</b> &bull; Scholar Growth & Development Report", title_style),
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}<br/><b>Authority:</b> VRCF Board", subtitle_style)
        ],
        [
            Paragraph("Vasumathi Ramaswami Centenary Foundation — Higher Education Mentorship Program", subtitle_style),
            ""
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.0 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # Divider Line
    line_table = Table([[""]], colWidths=[7.2 * inch], rowHeights=[2])
    line_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), primary_color)]))
    elements.append(line_table)
    elements.append(Spacer(1, 12))

    # 2. Scholar Identification Matrix
    student_info_data = [
        [
            Paragraph("<b>Scholar Name:</b>", body_style), Paragraph(student.name, body_bold),
            Paragraph("<b>VRCF ID:</b>", body_style), Paragraph(student.vrcf_id, body_bold)
        ],
        [
            Paragraph("<b>Cohort:</b>", body_style), Paragraph(student.cohort, body_style),
            Paragraph("<b>Current Year:</b>", body_style), Paragraph(student.year_of_study, body_style)
        ],
        [
            Paragraph("<b>Course of Study:</b>", body_style), Paragraph(student.course_name, body_style),
            Paragraph("<b>Residence Mode:</b>", body_style), Paragraph(student.hostel_or_dayscholar or "Dayscholar", body_style)
        ],
        [
            Paragraph("<b>Institution:</b>", body_style), Paragraph(student.college_name_district, body_style),
            Paragraph("<b>Assigned Mentor:</b>", body_style), Paragraph(assessor_name, body_style)
        ]
    ]
    info_table = Table(student_info_data, colWidths=[1.3 * inch, 2.3 * inch, 1.3 * inch, 2.3 * inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), surface_bg),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # 3. Vision & Strategic Goals
    vision = getattr(student, 'vision', None)
    if vision:
        elements.append(Paragraph("1. Personal Vision & Strategic Aims", section_heading))
        aim_text = vision.personal_aim or "Dedicated to academic distinction and ethical leadership."
        vision_text = vision.vision_statement or "Developing analytical rigor and contributing to community development."
        
        vision_data = [
            [Paragraph("<b>Guiding Aim:</b>", body_style), Paragraph(aim_text, body_style)],
            [Paragraph("<b>Vision Statement:</b>", body_style), Paragraph(vision_text, body_style)],
            [Paragraph("<b>Career Goals:</b>", body_style), Paragraph(vision.career_goals or "Professional leadership", body_style)]
        ]
        vision_table = Table(vision_data, colWidths=[1.4 * inch, 5.8 * inch])
        vision_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(vision_table)
        elements.append(Spacer(1, 10))

    # 4. Competency Development Profile
    elements.append(Paragraph("2. Evaluated Competency Development", section_heading))
    assessments = CompetencyAssessment.objects.filter(student=student).select_related('competency', 'assessor').order_by('-assessed_date')

    if assessments.exists():
        comp_rows = [[
            Paragraph("<b>Competency</b>", table_header),
            Paragraph("<b>Assessment Source</b>", table_header),
            Paragraph("<b>Assessed Level</b>", table_header),
            Paragraph("<b>Score</b>", table_header),
            Paragraph("<b>Observed Evidence / Feedback</b>", table_header)
        ]]
        for a in assessments[:8]:
            source_badge = "Mentor Official" if a.source == 'MENTOR' else "AI Formative"
            score_text = f"{a.score}/10" if a.score else "-"
            comp_rows.append([
                Paragraph(a.competency.name, body_bold),
                Paragraph(source_badge, body_style),
                Paragraph(a.get_level_display(), body_style),
                Paragraph(score_text, body_style),
                Paragraph(a.feedback or a.evidence or "Demonstrated competency.", body_style)
            ])
        comp_table = Table(comp_rows, colWidths=[1.5 * inch, 1.1 * inch, 1.1 * inch, 0.7 * inch, 2.8 * inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), surface_bg),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(comp_table)
    else:
        elements.append(Paragraph("<i>No formal evaluations published yet. Competencies are actively being developed through ongoing assignments.</i>", body_style))
    elements.append(Spacer(1, 12))

    # 5. Completed Submissions & Mentor Feedback
    elements.append(Paragraph("3. Mentor Assignments & Submissions History", section_heading))
    submissions = TaskSubmission.objects.filter(student=student).select_related('task', 'reviewed_by').order_by('-submitted_at')

    if submissions.exists():
        sub_rows = [[
            Paragraph("<b>Assignment Title</b>", table_header),
            Paragraph("<b>Submitted On</b>", table_header),
            Paragraph("<b>Status</b>", table_header),
            Paragraph("<b>Rating</b>", table_header),
            Paragraph("<b>Mentor Feedback Summary</b>", table_header)
        ]]
        for s in submissions[:6]:
            rating_text = f"{s.mentor_rating}/5" if s.mentor_rating else "Under Review"
            status_text = "Reviewed" if s.reviewed_at else ("Draft" if s.is_draft else "Submitted")
            feedback_text = s.mentor_feedback or s.student_remarks or "Submission recorded."
            sub_rows.append([
                Paragraph(s.task.title, body_bold),
                Paragraph(s.submitted_at.strftime('%b %d, %Y'), body_style),
                Paragraph(status_text, body_style),
                Paragraph(rating_text, body_style),
                Paragraph(feedback_text[:120], body_style)
            ])
        sub_table = Table(sub_rows, colWidths=[1.8 * inch, 1.0 * inch, 0.9 * inch, 0.8 * inch, 2.7 * inch])
        sub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), surface_bg),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(sub_table)
    else:
        elements.append(Paragraph("<i>No assignments submitted yet for this academic semester.</i>", body_style))
    elements.append(Spacer(1, 16))

    # 6. Foundation Sign-off Footer
    sign_data = [
        [
            Paragraph("____________________________<br/><b>Assigned Lead Mentor</b><br/>VRCF Mentorship Board", body_style),
            Paragraph("____________________________<br/><b>Foundation Trustee</b><br/>VRCF Executive Committee", body_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[3.6 * inch, 3.6 * inch])
    sign_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(KeepTogether([sign_table]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
