from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def add_title_to_pdf(input_pdf, output_pdf, title, subtitle, footer_text):
    # Open the existing PDF
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Get the first page size
    first_page = reader.pages[0]
    width, height = float(first_page.mediabox.width), float(first_page.mediabox.height)


    # Create a blank PDF with overlay text
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFillColor("#233630")
    can.setStrokeColor("#233630")

    # Set fonts
    can.setFont("Helvetica", 42)
    title_x, title_y = width / 2, height / 2 + 40  # Centered above the middle
    can.drawCentredString(title_x, title_y, title)

    # Draw a dividing line just below the title
    line_x1, line_x2 = 100, width - 100
    line_y = title_y - 20  # Just below the title
    can.line(line_x1, line_y, line_x2, line_y)

    # Set font for subtitle
    can.setFont("Helvetica", 20)
    subtitle_x, subtitle_y = width / 2, line_y - 30  # Centered and slightly below the line
    can.drawCentredString(subtitle_x, subtitle_y, subtitle)

    # Footer text (Bottom Left Corner)
    can.setFillColor('#70757A')  # Footer text in gray
    can.setFont("Helvetica", 9)
    footer_x, footer_y = 20, 30  # 40px from left, 30px from bottom

    # Split text manually by \n and draw each line separately
    for line in footer_text.split("\n"):
        can.drawString(footer_x, footer_y, line)
        footer_y -= 10  # Move up for the next line



    can.save()
    packet.seek(0) # Move to the beginning of the buffer

    # Merge with original PDF
    overlay = PdfReader(packet)
    first_page.merge_page(overlay.pages[0])
    writer.add_page(first_page)

    # Save the new PDF
    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)

    print(f"PDF '{output_pdf}' created with title and subtitle.")

# Example usage
add_title_to_pdf(r"C:\Users\feder\PycharmProjects\make_client_reports\inputs\LDT template.pdf", "cover.pdf",
                 "Análisis de Cartera", "Tenencia Consolidada y Desglose",
                 footer_text="Luis Domingo Trucco S.A. \n"
                             "Agente de Liquidación y Compensación y \n"
                             "Agente de Negociación Propio registrado bajo el Nº 216 de la CNV")
