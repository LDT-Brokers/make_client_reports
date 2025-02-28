from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.platypus import PageBreak
import io
from PIL import Image as PILImage
from reportlab.platypus import Spacer
from create_pdf.aux_functions import merge_pdfs
from typing import Literal
from reportlab.platypus import Paragraph
from statistics import median
from reportlab.lib.enums import TA_CENTER  # Import alignment constants

def format_number_spanish(number):
    if isinstance(number, int):
        return f"{number:,}".replace(",", ".")
    elif isinstance(number, float):
        formatted = f"{number:,.2f}".rstrip("0").rstrip(".")
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return number

class PDFReport:
    def __init__(self, filename, logo_path, cover_path, page_size=A4):
        self.header_height = 60
        self.filename = str(filename)
        self.logo_path = logo_path
        self.page_size = page_size
        self.margins = 40
        # dark green, green, gray, white
        self.colors = ["#233630", "#425F56", '#BBC3C1', '#F1F1F1']
        self.font = 'Helvetica'
        self.cover_path = cover_path
        self.colors = [HexColor(x) for x in self.colors]
        self.document = SimpleDocTemplate(self.filename, pagesize=self.page_size,
                                          rightMargin=self.margins, leftMargin=self.margins,
                                          topMargin=self.header_height, bottomMargin=self.margins)


        self.elements = []
        self.styles = getSampleStyleSheet()

    def add_title(self, title, font_size=18, alignment: Literal[0, 1, 2, 4, "left", "center", "centre", "right", "justify"]=0, with_space=True):
        """Add title to the PDF with optional font size and alignment."""
        if with_space:
            space_after = 20
        else:
            space_after = 0
        title_style = ParagraphStyle(
            name="TitleStyle",
            fontSize=font_size,
            alignment=alignment,
            fontName=self.font+"-Bold",
            spaceBefore=12,
            textColor=self.colors[0],
            spaceAfter=space_after
        )
        title_paragraph = Paragraph(title, title_style)
        self.elements.append(title_paragraph)

    def add_text(self, text, font_size=12,
                 alignment:Literal[0, 1, 2, 4, "left", "center", "centre", "right", "justify"]=0,
                 with_space=True, text_color=None, bold=False,  **kwargs):
        """Add plain text to the PDF with optional font size and alignment."""
        text_color = text_color or self.colors[0]
        font = self.font if not bold else self.font + '-Bold'
        text_style = ParagraphStyle(
            name="TextStyle",
            fontSize=font_size,
            alignment=alignment,
            fontName=font,
            textColor=text_color,
            **kwargs
        )
        text_paragraph = Paragraph(text, text_style, encoding='latin1')
        self.elements.append(text_paragraph)
        # Add space after text
        if with_space:
            self.add_space()

    def add_space(self, height=20):
        """Add custom space to the PDF."""
        self.elements.append(Spacer(1, height))

    def add_divider(self, thickness=1):
        """Add a horizontal divider to the PDF."""
        divider_data = [[""]]
        divider_style = [
            ("LINEBELOW", (0, 0), (-1, -1), thickness, self.colors[0]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]
        w = self.page_size[0] - 2 * self.margins
        divider_table = Table(divider_data, colWidths=[w])
        divider_table.setStyle(divider_style)
        self.elements.append(divider_table)


    def new_page(self):
        """Add a new page to the PDF."""
        self.elements.append(PageBreak())


    def add_df(self, df, bold_rows=None):
        """Add DataFrame as a table to the PDF."""
        df = df.copy()
        number_cols = df.select_dtypes(include=['number']).columns
        df = df.fillna("-")
        bold_rows = bold_rows or []
        df[number_cols] = df[number_cols].map(format_number_spanish)
        table_data = [df.columns.to_list()] + df.values.tolist()
        font_size = 10

        page_width, _ = self.page_size


        df_str = df.astype(str)
        lengths = [[len(str(val)) for val in df_str[col]] for col in df_str.columns]
        modes = [median(length) for length in lengths]
        sum_modes = sum(modes)
        total_width = (page_width - 2 * self.margins)
        col_widths = [ci * total_width / sum_modes for ci in modes]


        # Convert all cells to Paragraphs for wrapping, take into account that these settings override any table
        # setting, so set the parameters here
        # Define styles for different text elements
        header_style = getSampleStyleSheet()["Normal"].clone('HeaderStyle')
        header_style.fontName = self.font + '-Bold'
        header_style.fontSize = font_size
        header_style.textColor = self.colors[3]
        header_style.wordWrap = "CJK"
        header_style.alignment = TA_CENTER  # Ensure paragraph is center-aligned

        body_style = getSampleStyleSheet()["Normal"].clone('BodyStyle')
        body_style.fontName = self.font
        body_style.fontSize = font_size
        body_style.wordWrap = "CJK"
        body_style.alignment = TA_CENTER  # Ensure paragraph is center-aligned

        # Apply styles to table data
        table_data = [
             [Paragraph(str(cell), header_style) for cell in table_data[0]]  # Apply header style
                     ] + [
             [Paragraph(str(cell), body_style) for cell in row] for row in table_data[1:]
                         # Apply body style
                     ]

        table = Table(table_data, colWidths=col_widths)
        table_style  = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors[1]),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors[0]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        for row_idx in bold_rows:
            table_style.add('BACKGROUND', (0, row_idx + 1), (-1, row_idx + 1), self.colors[2])

        table.setStyle(table_style)
        self.elements.append(table)
        # Add space after the table
        self.elements.append(Spacer(1, 12))

    def add_chart(self, fig):
        """Add chart as an image to the PDF."""
        img_stream = io.BytesIO()
        fig.savefig(img_stream, format="png")
        img_stream.seek(0)
        img = Image(img_stream)
        # Scale
        orig_width, orig_height = img.imageWidth, img.imageHeight
        max_width = 520
        max_height = 680
        scale_w = max_width / orig_width
        scale_h = max_height / orig_height
        scale_factor = min(scale_w, scale_h)  # Ensure it fits both width and height
        img.drawWidth = orig_width * scale_factor
        img.drawHeight = orig_height * scale_factor

        self.elements.append(img)
        # Add space after the chart
        self.elements.append(Spacer(1, 12))

    def footer(self, canvas, doc):
        """Add footer with page number."""
        canvas.saveState()
        canvas.setFont(self.font, 10)
        page_width, _ = self.page_size
        canvas.drawString(page_width-self.margins*2, 20, f"P. {doc.page}")
        canvas.restoreState()

    def header(self, canvas, doc):

        # Load the image
        pil_img = PILImage.open(self.logo_path)
        img_width, img_height = pil_img.size
        aspect_ratio = img_height / img_width

        # Desired dimensions
        desired_height = 30  # Slightly smaller than header height
        desired_width = desired_height / aspect_ratio

        # Page dimensions
        page_width, page_height = self.page_size
        x_position = page_width - desired_width - 20  # Right-aligned with margin
        y_position = page_height - desired_height - 10  # Top-aligned with a small margin

        # Draw the image
        img = Image(self.logo_path, width=desired_width, height=desired_height)
        img.drawOn(canvas, x_position, y_position)


    def build_pdf(self):
        """Build and save the PDF document."""
        self.document.build(self.elements, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        merge_pdfs(self.cover_path, self.filename, self.filename)

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        self.header(canvas, doc)
        self.footer(canvas, doc)
