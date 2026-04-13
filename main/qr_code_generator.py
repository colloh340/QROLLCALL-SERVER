import qrcode
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import tempfile
from reportlab.lib.colors import black
from . report_pdf_generator import add_footer, create_pdf_header
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Frame, PageTemplate, Spacer


class QR:
    def __init__(self, class_attendance_hashed_values, unit_code, date):
        self.class_attendance_hashed_values = class_attendance_hashed_values
        self.unit_code = unit_code
        self.date = date
    
    def generate_qr_code(self):
        try:

            qr = qrcode.QRCode(
                version=1,  # Smallest size for your data
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low error correction (sufficient for small data)
                box_size=10,  # Size of each box in the QR code grid
                border=4,  # Default border size
            )
            qr.add_data(self.class_attendance_hashed_values)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            #img.save("hashed_qr.png")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            buffered.seek(0) 
            
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Return both base64 and PDF file byte stream
            return img_base64

        except Exception as e:
            return None
        
    def generate_qr_pdf(self, qr_image_bytes):
        try:
            file_name = f"{self.unit_code}_{self.date}_qr_code.pdf"

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'

            pdf = SimpleDocTemplate(response, pagesize=letter)
            frame = Frame(40, 70, letter[0] - 80, letter[1] - 140, id='normal')

            # Decode base64 to BytesIO
            qr_bytes = base64.b64decode(qr_image_bytes)
            qr_image_stream = BytesIO(qr_bytes)

            # Define the page template with footer
            template = PageTemplate(id='test', frames=frame, onPage=add_footer)
            pdf.addPageTemplates([template])
            elements = []

            # Add header
            elements.append(create_pdf_header(f"QR Code for {self.unit_code}"))

            # Convert BytesIO image to ReportLab image
            qr_img = Image(qr_image_stream, width=200, height=200)

            # Compute remaining height and add spacer
            available_height = letter[1] - 200 - 200  # Page height - header - footer
            spacer_height = available_height / 2 - 100  # Center vertically

            elements.append(Spacer(1, max(spacer_height, 0)))  # Push image down

            # Center QR Code in a table
            qr_table = Table([[qr_img]], colWidths=[letter[0] - 80], rowHeights=[200])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(qr_table)

            pdf.build(elements)

            return True, response
        except Exception as e:
            print(f"Error: {e}")
            return False, {
                "message": "Something went wrong",
                "status": 500
            }