from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.platypus import PageBreak
import io
from PIL import Image as PILImage
from reportlab.platypus import Spacer
from create_pdf.aux_functions import merge_pdfs, crear_grafico, add_subtotals, add_totals, get_total_rows
from create_pdf.plotting_functions import create_grafico_multiple

def format_number_spanish(number):
    if isinstance(number, int):
        return f"{number:,}".replace(",", ".")
    else:
        formatted = f"{number:,.2f}".rstrip("0").rstrip(".")
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

class PDFReport:
    def __init__(self, filename, logo_path, cover_path, page_size=A4):
        self.header_height = 60
        self.filename = filename
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

    def add_title(self, title, font_size=18, alignment=0, with_space=True):
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

    def add_text(self, text, font_size=12, alignment=0, with_space=True, text_color=None, bold=False,  **kwargs):
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
        df = df.fillna("-")
        bold_rows = bold_rows or []
        df[df.select_dtypes(include=['number']).columns] = df.select_dtypes(include=['number']).map(format_number_spanish)
        table_data = [df.columns.to_list()] + df.values.tolist()
        font_size = 10 if len(df.columns) <= 10 else 8  # Reduce font size if more than 10 columns

        page_width, _ = self.page_size


        df_str = df.astype(str)
        lengths = [[len(str(val)) for val in df_str[col]] for col in df_str.columns]
        col_lens = [len(c) for c in df_str.columns]
        modes = [max(length) for length in lengths]
        modes_2 = [max(c1,c2) for c1,c2 in zip(col_lens, modes)]
        sum_modes = sum(modes_2)
        total_width = (page_width - 2 * self.margins)
        col_widths = [ci * total_width / sum_modes for ci in modes_2]

        table = Table(table_data, colWidths=col_widths)
        table_style  = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors[1]),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors[3]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors[0]),
            ('FONTNAME', (0, 0), (-1, 0), self.font + '-Bold'),  # Column headers bold
            ('FONTNAME', (0, 1), (-1, -1), self.font),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center the column headers
            # ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Align the first column to the left

        ])
        for row_idx in bold_rows:
            # Adjust for 1-based index because the header is row 0
            table_style.add('BACKGROUND', (0, row_idx + 1), (-1, row_idx + 1), self.colors[2])
            #table_style.add('FONTNAME', (0, row_idx + 1), (-1, row_idx + 1), self.font + '-Bold')

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




if __name__ == '__main__':
    # Usage Example
    import pandas as pd
    import numpy as np


    # Example dataframe with more columns
    random_data = np.random.randn(200, 3) * 2500 + 2500  # Scale and shift to get values in the range [-5000, 5000]
    random_data = np.clip(random_data, 0, 5000)  # Clip values to the range [0, 5000]
    random_data = np.round(random_data).astype(int)  # Round to integers
    df_ex = pd.DataFrame(random_data, columns=[f'Column{i+1}' for i in range(3)])

    df_tenencia_total = pd.DataFrame({
        "CLASIFICACION": ["Activos", "Moneda"],
        "TENENCIA [US$]": [2_978_650.34, 852_460.07]
    })
    df_resumen_activos = pd.DataFrame({
        "CLASIFICACION": [
            "ETFs",
            "Renta Fija Extranjera",
            "Renta Fija Local",
            "Renta Variable Extranjera",
            "Renta Variable Local"
        ],
        "TENENCIA [US$]": [
            548_885.19,
            1_021_795.00,
            977.95,
            1_275_936.56,
            131_055.64,
        ],
        "PART. [%]": [18.43, 34.30, 0.03, 42.84, 4.40]
    })

    n = 50  # Número de filas
    activos = [f"Activo_{i}" for i in range(n)]
    tenencias = np.random.randint(1, 1000, size=n)
    tipo_activo = np.random.choice(["Acción", "Bono", "Fondo", "ETF", "Derivado"], size=n)
    local_extranjera = np.random.choice(["Local", "Extranjera"], size=n)
    fija_variable = np.random.choice(["Fija", "Variable"], size=n)

    df_assets = pd.DataFrame({
        "Activo": activos,
        "Tenencia": tenencias,
        "Tipo de Activo": tipo_activo,
        "Local o Extranjera": local_extranjera,
        "Fija o Variable": fija_variable
    })
    df_assets['Tenencia'] = df_assets['Tenencia'].astype(int)
    df_assets2 = add_subtotals(df_assets, group_by_column='Tipo de Activo')

    # Create and build the PDF report
    pdf_report = PDFReport("output_report.pdf", "../inputs/logo-login.png",
                           cover_path="../inputs/cover.pdf")
    pdf_report.add_text("Tenencia Total 1174-3219", font_size=24, with_space=False, bold=True)
    tc = 1228.18
    tc = format_number_spanish(int(tc))
    pdf_report.add_text(f"USD/ARS: {tc} - 28/05/2024", font_size=14, with_space=False, alignment=2, text_color=HexColor('#70757A'))
    pdf_report.add_divider()


    pdf_report.add_title("Tenencia Total")

    df_resumen_activos2 = add_totals(df_resumen_activos)
    pdf_report.add_df(df_resumen_activos2, get_total_rows(df_resumen_activos2))

    pdf_report.add_title("Resumen de Activos")
    df_resumen_activos2 = add_totals(df_resumen_activos)

    pdf_report.add_df(df_resumen_activos2, get_total_rows(df_resumen_activos2))

    pdf_report.add_text("This is a sample sales report.")
    pdf_report.add_df(df_assets2, get_total_rows(df_assets2))  # Add the DataFrame
    fig_ex = create_grafico_multiple(
        df=df_assets,
        agg_cols=["Tipo de Activo", "Local o Extranjera", "Fija o Variable"],
        target_col="Tenencia",
        grid_size= (4, 2),
        plot_positions=[(slice(None), 0), (slice(0,2), 1), (slice(2,4), 1)],
        fig_types=['pie', 'pie', 'pie']
    )
    pdf_report.add_chart(fig_ex)  # Add the chart


    fig_ex = create_grafico_multiple(
        df=df_assets,
        agg_cols=["Activo"],
        target_col="Tenencia",
        grid_size= (4,2),
        plot_positions=[(slice(None), slice(None))],
        fig_types=['bar']

    )
    pdf_report.add_chart(fig_ex)  # Add the chart

    pdf_report.build_pdf()
