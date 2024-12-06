from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
import matplotlib.pyplot as plt
from reportlab.platypus import PageBreak

import io
from PIL import Image as PILImage
from reportlab.platypus import Spacer

class PDFReport:
    def __init__(self, filename, logo_path):
        self.header_height = 80
        self.filename = filename
        self.logo_path = logo_path
        self.document = SimpleDocTemplate(self.filename, pagesize=letter, rightMargin=28, leftMargin=28, topMargin=self.header_height, bottomMargin=28)

        self.elements = []
        self.styles = getSampleStyleSheet()

    def add_title(self, title, font_size=18, alignment=0):
        """Add title to the PDF with optional font size and alignment."""
        title_style = ParagraphStyle(
            name="TitleStyle",
            fontSize=font_size,
            alignment=alignment,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            textColor=colors.black
        )
        title_paragraph = Paragraph(f"<u>{title}</u>", title_style)
        self.elements.append(title_paragraph)
        # Add some space after the title
        self.elements.append(Spacer(1, 24))  # Default space after title

    def add_text(self, text, font_size=12, alignment=0):
        """Add plain text to the PDF with optional font size and alignment."""
        text_style = ParagraphStyle(
            name="TextStyle",
            fontSize=font_size,
            alignment=alignment,
            fontName="Helvetica",
            textColor=colors.black
        )
        text_paragraph = Paragraph(text, text_style)
        self.elements.append(text_paragraph)
        # Add space after text
        self.elements.append(Spacer(1, 12))

    def add_space(self, height):
        """Add custom space to the PDF."""
        self.elements.append(Spacer(1, height))

    def add_divider(self, color=colors.black, thickness=1):
        """Add a horizontal divider to the PDF."""
        from reportlab.platypus import Table
        divider_data = [[""]]
        divider_style = [
            ("LINEBELOW", (0, 0), (-1, -1), thickness, color),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]
        divider_table = Table(divider_data, colWidths=[500])
        divider_table.setStyle(divider_style)
        self.elements.append(divider_table)

    def new_page(self):
        """Add a new page to the PDF."""
        self.elements.append(PageBreak())


    def add_df(self, df):
        """Add DataFrame as a table to the PDF."""
        table_data = [df.columns.to_list()] + df.values.tolist()
        font_size = 10 if len(df.columns) <= 10 else 8  # Reduce font size if more than 10 columns

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center the column headers
        ]))
        self.elements.append(table)
        # Add space after the table
        self.elements.append(Spacer(1, 12))

    def add_chart(self, fig):
        """Add chart as an image to the PDF."""
        img_stream = io.BytesIO()
        fig.savefig(img_stream, format="png")
        img_stream.seek(0)
        img = Image(img_stream)
        img.width = 400
        img.height = 300
        self.elements.append(img)
        # Add space after the chart
        self.elements.append(Spacer(1, 12))

    def footer(self, canvas, doc):
        """Add footer with page number."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(500, 20, f"Page {doc.page}")
        canvas.restoreState()


    def header(self, canvas, doc):
        """Add header with business logo."""
        # Open the image using PIL to get the original dimensions
        pil_img = PILImage.open(self.logo_path)
        img_width, img_height = pil_img.size

        # Calculate the height maintaining the aspect ratio
        aspect_ratio = img_height / img_width

        desired_width = self.header_height / aspect_ratio

        # Create a reportlab Image object
        img = Image(self.logo_path, width=desired_width, height=self.header_height)

        # Draw the image at the desired location
        img.drawOn(canvas, 20, 750)

    def build_pdf(self):
        """Build and save the PDF document."""
        self.document.build(self.elements, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        self.header(canvas, doc)
        self.footer(canvas, doc)

if __name__ == '__main__':
    # Usage Example
    import pandas as pd
    import numpy as np

    # Create some example data for the chart
    data = {'Category': ['A', 'B', 'C', 'D', 'E'], 'Value': [10, 20, 15, 30, 25]}
    df = pd.DataFrame(data)

    # Create a simple bar chart using matplotlib
    fig, ax = plt.subplots(figsize=(6, 4))  # 6x4 inches size for the chart
    ax.bar(df['Category'], df['Value'], color='skyblue')
    ax.set_title('Example Bar Chart')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')

    # Example dataframe with more columns
    random_data = np.random.randn(200, 3) * 2500 + 2500  # Scale and shift to get values in the range [-5000, 5000]
    random_data = np.clip(random_data, 0, 5000)  # Clip values to the range [0, 5000]
    random_data = np.round(random_data).astype(int)  # Round to integers
    df = pd.DataFrame(random_data, columns=[f'Column{i+1}' for i in range(3)])

    # Create and build the PDF report
    pdf_report = PDFReport("output_report.pdf", r"C:\Users\feder\Pictures\LDT Fondo Blanco.png")
    pdf_report.add_title("Sales Report")
    pdf_report.add_text("This is a sample sales report.")
    pdf_report.add_df(df)  # Add the DataFrame
    pdf_report.add_chart(fig)  # Add the chart

    pdf_report.new_page()
    pdf_report.add_title("Sales Report2")
    pdf_report.add_divider()
    pdf_report.add_chart(fig)  # Add the chart

    pdf_report.build_pdf()
