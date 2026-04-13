from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, PageTemplate, Image,Paragraph, Spacer
from datetime import datetime
from .utils import home_tz, image_logo_path
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from functools import partial

def generate_attendance_pdf(report):
    try:
        students = report["students"]
        caption = report["caption"]
        
        empty_student = {
            "registration_number": "",
            "name": "_",
            "check_in_time": "",
            "time_status": "_",
            "status": "_"
        }

        # Show 5 empty rows if no students exist
        if isinstance(students, list) and len(students) < 10:
            missing = 10 - len(students)
            for _ in range(missing):
                students.append(empty_student.copy())

        file_name = f"{report["unit_code"]}_{report["date"]}_attendance_report.pdf"

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        pdf = SimpleDocTemplate(response, pagesize=A4, topMargin=30, bottomMargin=30)

        frame = Frame(40, 40, A4[0] - 80, A4[1] - 100, id='normal')

        # Define the page template with footer
        template = PageTemplate(id='test', frames=frame, onPage=add_footer)
        pdf.addPageTemplates([template])

        elements = []

        elements.append(create_pdf_header(f"Class Attendance Form"))

        # Attendance Summary
        summary_data = [
            ["Unit Code:", f"{report['unit_code']}", "", "Date:", f"{report['date']}"],
            ["Unit Name:", f"{report['unit_name']}", "", "Start:", f"{report['start_time']}"],
            ["Lecturer:", f"{report['lecturer']}", "", "End:", f"{report['end_time']}"],
            ["Present:", f"{report['present_count']}", "","Absent:", f"{report['absent_count']}"]
        ]
        summary_table = Table(summary_data, colWidths=[80, 150, 30, 80, 80])

        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ]))
        elements.append(summary_table)

        # Add spacing
        elements.append(Table([[""]], rowHeights=10))

        styles = getSampleStyleSheet()
        caption_style = styles["Normal"]
        caption_style.fontSize = 9  # Small font size
        caption_style.textColor = colors.grey  # Light color
        caption_style.leading = 12  # Spacing between lines

        # Add the caption as a paragraph
        caption_table = Table([[Paragraph(caption, caption_style)]])

        # Style it to match table indentation
        caption_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(caption_table)
        # Add some space after the caption
        elements.append(Table([[""]], rowHeights=5))

        # Table Header
        table_data = [["#", "Student", "Timestamp", "Present/Absent"]]

        # Add students dynamically
        
        for index, student in enumerate(students, start=1):  # start=1 makes index start from 1
            formatted_time = "N/A"
            try:
                timestamp = datetime.fromisoformat(str(student['check_in_time']))
                localized_time = timestamp.astimezone(home_tz)
                formatted_time = localized_time.strftime("%I:%M %p")
            except Exception as e:
                formatted_time = ""
            table_data.append([
                index,  # Current index
                f"{student['registration_number']}\n{student['name']}",
                f"{formatted_time}\n{student['time_status']}",
                student["status"]
            ])


        # Create Table
        table = Table(table_data, colWidths=[30, 200, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('VALIGN', (1, 1), (-2, -2), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(table)

        # Build the PDF
        pdf.build(elements)

        return True, response
    
    except Exception as e:
        print(f"Error {e}")
        return False, {
            "message": f"Error: {e}",
            "status":500
        }
    
def generate_staff_unit_report(report):
    try:
        units_list = report.get("units", [])
        unit = units_list[0] if units_list else {}
        report_type = report.get("report_type", "all")
        staff_name = report.get("staff_name", "Unknown")
        unit_code = unit.get("unit_code", "N/A")
        unit_name = unit.get("unit_name", "Not assigned")
        total_classes = unit.get("total_classes", 0)
        completed_classes = unit.get("completed_classes", 0)
        uncompleted_classes = unit.get("uncompleted_classes", 0)
        compliance = unit.get("total_compliance_percentage", "0")
        defaulters = unit.get("total_non_compliance_percentage", "0")
        completed_classes_list = unit.get("completed_classes_list", [])
        uncompleted_classes_list = unit.get("uncompleted_classes_list", [])
        compliant_students = unit.get("compliant_students", [])
        non_compliant_students = unit.get("non_compliant_students", [])

        compliant_student_data = [
            {"registration_number": student["registration_number"], "name": student["name"], "present": student["total_attended"], "absent": student["total_absent"], "compliance": f"{student["compliance_percentage"]}%"}
            for student in compliant_students
        ]
        non_compliant_student_data = [
            {"registration_number": student["registration_number"], "name": student["name"], "present": student["total_attended"], "absent": student["total_absent"], "compliance": f"{student["compliance_percentage"]}%"}
            for student in non_compliant_students
        ]
        completed_classes_data = [
            {"unit": unit_code, "date": lecture["attendance_date"], "time": f"{lecture['start_time']} - {lecture['end_time']}", "status": "Complete"}
            for lecture in completed_classes_list
        ]
        uncompleted_classes_data = [
            {"unit": unit_code, "date": lecture["attendance_date"], "time": f"{lecture['start_time']} - {lecture['end_time']}", "status": "Incomplete"}
            for lecture in uncompleted_classes_list
        ]


        file_name = f"{unit_code}_{staff_name}_unit_report.pdf"

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        pdf = SimpleDocTemplate(response, pagesize=A4, topMargin=30, bottomMargin=30)

        frame = Frame(40, 40, A4[0] - 80, A4[1] - 100, id='normal')

        custom_header = partial(create_header_two, title_text=f"{unit_code} report")

        template = PageTemplate(id='test', frames=frame, onPage=custom_header, onPageEnd=add_footer)        
        pdf.addPageTemplates([template])

        elements = [Spacer(1, 50)]

        # Define a custom style for better formatting
        styles = getSampleStyleSheet()
        bold_style = ParagraphStyle(
            "BoldStyle",
            parent=styles["Normal"],
            fontSize=12,
            leading=14,
            spaceAfter=5,
            # textColor=colors.darkblue
        )

        normal_style = ParagraphStyle(
            "NormalStyle",
            parent=styles["Normal"],
            fontSize=12,
            leading=14,
            spaceAfter=5
        )

        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>Lecturer:</b> {staff_name}", bold_style))
        elements.append(Paragraph(f"<b>Unit Name:</b> {unit_name}", bold_style))

        elements.append(Paragraph(f"<b>Total Classes:</b> {total_classes}", normal_style))
        elements.append(Paragraph(f"<b>Completed Classes:</b> {completed_classes}", normal_style))
        elements.append(Paragraph(f"<b>Uncompleted Classes:</b> {uncompleted_classes}", normal_style))

        elements.append(Paragraph(f"<b>Compliance:</b> {compliance}%", normal_style))
        elements.append(Paragraph(f"<b>Defaulters:</b> {defaulters}%", normal_style))

        elements.append(Spacer(1, 5))
        if report_type == "completed":
            elements += generate_lectures_table("Completed lectures", completed_classes_data, True)
        elif report_type == "non-compliant":
            elements += generate_student_table("Defaulters Report", non_compliant_student_data, False)
        elif report_type == "compliant":
            elements += generate_student_table("Compliance Report", compliant_student_data, True)
        elif report_type == "uncompleted":
            elements += generate_lectures_table("Incompleted lectures", uncompleted_classes_data, False)
        else:
            elements += generate_lectures_table("Completed lectures", completed_classes_data, True)
            elements += generate_lectures_table("Incompleted lectures", uncompleted_classes_data, False)
            elements += generate_student_table("Compliance Report", compliant_student_data, True)
            elements += generate_student_table("Defaulters Report", non_compliant_student_data, False)
            

        pdf.build(elements)

        return True, response
    except Exception as e:
        print(f"Error {e}")
        return False, {
            "message": f"Error: {e}",
            "status":500
        }
    
def generate_lectures_table(caption, lectures, completed = True):
    empty_lecture = {
        "unit": "_",
        "date": "_",
        "time": "_",
        "status": "_"
    }
    color = colors.darkgreen if completed else colors.darkred
    if isinstance(lectures, list) and len(lectures) < 5:
        lectures.extend([empty_lecture.copy() for _ in range(5 - len(lectures))])

    elements = [Spacer(1, 8)]
    styles = getSampleStyleSheet()
    

    title_style = styles["Title"]
    title_style.fontSize = 14
    title_style.alignment = 1
    title_style.textColor = color  # Different title color

    elements.append(Paragraph(f"<b>{caption}</b>", title_style))
    elements.append(Spacer(1, 5))

    table_data = [["#", "Unit", "Date", "Time", "Status"]]
    for index, lecture in enumerate(lectures, start=1):
        table_data.append([
            index,
            lecture["unit"],
            lecture["date"],
            lecture["time"],
            lecture["status"]
        ])

    table = Table(table_data, colWidths=[30, 120, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color),  # Different header color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Subtle alternate row color
    ]))
    
    elements.append(table)
    return elements


def generate_student_table(caption, students, compliance = True):
    empty_student = {
        "registration_number": "_",
        "name": "_",
        "present": "_",
        "absent": "_",
        "compliance": "_"
    }
    color = colors.darkblue if compliance else colors.darkred

    if isinstance(students, list) and len(students) < 5:
        students.extend([empty_student.copy() for _ in range(5 - len(students))])

    elements = [Spacer(1, 10)]
    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.fontSize = 14  # Larger font size for distinction
    title_style.alignment = 1  # Center align
    title_style.textColor = color  # Blue title color

    elements.append(Paragraph(f"<b>{caption}</b>", title_style))
    elements.append(Spacer(1, 5))

    table_data = [["#", "Student", "Present/Absent", "Compliance"]]
    for index, student in enumerate(students, start=1):
        is_empty_student = all(value == "_" for value in student.values())
        
        table_data.append([
            index,
            f"{student['registration_number']}\n{student['name']}" if not is_empty_student else "_",
            f"Present: {student['present']}\nAbsent: {student['absent']}" if not is_empty_student else "_",
            student["compliance"]
        ])

    table = Table(table_data, colWidths=[30, 220, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # White header text
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Increase header padding
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),  # Alternate row color
    ]))
    
    elements.append(table)
    return elements

def create_header_two(canvas, doc, title_text="Class Attendance Form"):
    """
    Creates a standard header for QROLLCALL PDFs with an image, system name, and document title.
    """
    # Create Image object (adjust size as needed)
    img = Image(image_logo_path, width=60, height=60)  # Resize image appropriately

    # Define table structure
    title = [
        ["",img],  # Image row
        ["", "QROLLCALL QUALITY MANAGEMENT SYSTEM"],  # System title row
        ["", title_text]  # Document title row
    ]

    # Create the table
    title_table = Table(title, colWidths=[60, 250], rowHeights=[60, 20, 15])

    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all content
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center content
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica-Bold'),  # Bold text
        ('FONTSIZE', (1, 1), (-1, -1), 14),  # Font size
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # Space below each row
    ]))


    # Get current Y position and draw the table
    width, height = doc.pagesize
    title_table.wrapOn(canvas, width, height)
    title_table.drawOn(canvas, 100, height - 100)  # Adjust position as needed

    # Draw a line below the header
    line_y_position = height - 110  # Position the line slightly below the table
    canvas.setStrokeColor(colors.black)  # Line color
    canvas.setLineWidth(1)  # Line thickness
    canvas.line(50, line_y_position, width - 50, line_y_position)  # Draw line across the page

def add_footer(canvas, doc):
    """
    Function to draw the footer on each page.
    """
    width, _ = letter  # Get page dimensions

    # Draw a horizontal line
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(40, 50, width - 40, 50)  # Line from left to right

    # Footer Text
    footer_text = "QROLLCALL QUALITY MANAGEMENT SYSTEM"
    timestamp = f"Generated at: {datetime.now(tz=home_tz).strftime('%B %d, %Y at %I:%M %p')}"

    # Set font and size
    canvas.setFont("Helvetica", 8)

    # Position footer text and timestamp aligned to the right
    canvas.drawRightString(width - 40, 40, footer_text)
    canvas.drawRightString(width - 40, 30, timestamp)

def create_pdf_header(title_text="Class Attendance Form"):
    """
    Creates a standard header for QROLLCALL PDFs with an image, system name, and document title.
    """
    # Create Image object (adjust size as needed)
    img = Image(image_logo_path, width=60, height=60)  # Resize image appropriately

    # Define table structure
    title = [
        ["",img],  # Image row
        ["", "QROLLCALL QUALITY MANAGEMENT SYSTEM"],  # System title row
        ["", title_text]  # Document title row
    ]

    # Create the table
    title_table = Table(title, colWidths=[60, 400], rowHeights=[60, 20, 20])

    # Apply styling
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all content
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center content
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica-Bold'),  # Bold text
        ('FONTSIZE', (1, 1), (-1, -1), 14),  # Font size
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Space below each row
    ]))

    return title_table


