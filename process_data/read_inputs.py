import pandas as pd
from pathlib import Path
from create_pdf.pdf_report_creator import PDFReport
from create_pdf.aux_functions import merge_pdfs, crear_grafico, add_subtotals, add_totals, get_total_rows


inputs_path = Path(__name__).parent.parent.joinpath('inputs')



df_tenencia = pd.read_excel(inputs_path.joinpath('tenencia_valorizada_inge.xlsx'))
cols = ['Comitente - Número','Tipo de Instrumento',	'Instrumento - Simbolo',	'Instrumento - Código Caja', 'Instrumento - Denominación',
'Cantidad',	'Fecha de Cotización',	'Cotización',	'Saldo Valorizado $']
df_tenencia=df_tenencia[cols].copy()
monedas = df_tenencia[~(df_tenencia['Instrumento - Denominación'].isna())&(df_tenencia['Instrumento - Código Caja'].isna())]['Instrumento - Denominación'].unique()

df_tenencia.dropna(subset=['Instrumento - Simbolo',	'Instrumento - Código Caja'], inplace=True)

df_tenencia['is_exterior'] = df_tenencia['Instrumento - Simbolo'].str.contains('_U')

df_tenencia_1 = df_tenencia[df_tenencia["Comitente - Número"] == 23012]
pdf_report = PDFReport("output_report2.pdf", "../inputs/logo-login.png",
                           cover_path="../inputs/cover.pdf")

pdf_report.add_text("Tenencia Total 1174-3219", font_size=24, with_space=False, bold=True)
tc = 1228
pdf_report.add_text(f"USD/ARS: {tc} - 28/05/2024", font_size=14, with_space=False, alignment=2, text_color=HexColor('#70757A'))
pdf_report.add_divider()

pdf_report.add_title("Tenencia Total")

df_tenencia_by_asset = df_tenencia_1.groupby('Tipo de Instrumento')['Saldo Valorizado $'].sum().reset_index()

pdf_report.add_df(df_tenencia_by_asset)

df_tenencia_1_str = df_tenencia_1[['Instrumento - Simbolo', 'Tipo de Instrumento', 'Cantidad', 'Cotización', 'Saldo Valorizado $']]
df_tenencia_1_str = add_subtotals(df_tenencia_1_str, group_by_column='Tipo de Instrumento', sum_columns=['Saldo Valorizado $'])
pdf_report.add_df(df_tenencia_1_str, bold_rows=get_total_rows(df_tenencia_1_str))

pdf_report.build_pdf()