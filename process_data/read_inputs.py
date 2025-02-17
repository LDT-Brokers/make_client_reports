import pandas as pd
from pathlib import Path
from create_pdf.pdf_report_creator import PDFReport
from create_pdf.aux_functions import  add_subtotals, add_totals, get_total_rows
from create_pdf.plotting_functions import create_grafico_multiple
from reportlab.lib.colors import HexColor

main_dir_path = Path(__file__).parent.parent
inputs_path = main_dir_path.joinpath('inputs')
outputs_path = main_dir_path.joinpath('outputs')


df_tenencia = pd.read_excel(inputs_path.joinpath('tenencia_valorizada_inge.xlsx'))
cols = ['Comitente - Número','Tipo de Instrumento',	'Instrumento - Simbolo',	'Instrumento - Código Caja', 'Instrumento - Denominación',
'Cantidad',	'Fecha de Cotización',	'Cotización',	'Saldo Valorizado $']
df_tenencia=df_tenencia[cols].copy()
df_tenencia.loc[
    ~(df_tenencia['Instrumento - Denominación'].isna()) & (df_tenencia['Instrumento - Código Caja'].isna()),
    'Tipo de Instrumento'
] = 'Moneda'
df_tenencia['Clasificacion'] = df_tenencia['Tipo de Instrumento'].apply(lambda x: 'Moneda' if x == 'Moneda' else 'Activo')
df_tenencia.dropna(subset=['Instrumento - Simbolo',	'Instrumento - Código Caja', 'Instrumento - Denominación'], how='all', inplace=True)
df_tenencia['is_exterior'] = df_tenencia['Instrumento - Simbolo'].str.contains('_U')
tc = 1228
df_tenencia['Saldo [USD]'] = df_tenencia['Saldo Valorizado $'] / tc
tenencia_col = 'Saldo [USD]'
df_tenencia = df_tenencia[df_tenencia[tenencia_col] >= 0.01].copy()


df_asset_master = pd.read_excel(inputs_path.joinpath('all_assets.xlsx'))


df_tenencia_1 = df_tenencia[df_tenencia["Comitente - Número"] == 7101].copy()
df_tenencia_1 = pd.merge(df_tenencia_1, df_asset_master, left_on='Instrumento - Código Caja', right_on='code_caja_val', how='left')



pdf_report = PDFReport(
    filename=outputs_path.joinpath("output_report2.pdf"),
    logo_path=inputs_path.joinpath("logo-login.png"),
    cover_path=inputs_path.joinpath("cover.pdf"))

pdf_report.add_text("Tenencia Total 1174-3219", font_size=24, with_space=False, bold=True)
pdf_report.add_text(f"USD/ARS: {tc} - 28/05/2024", font_size=14, with_space=False, alignment=2, text_color=HexColor('#70757A'))
pdf_report.add_divider()

pdf_report.add_title("Tenencia Total")
df_tenencia_by_clasificacion = df_tenencia_1.groupby('Clasificacion')[tenencia_col].sum().reset_index()
df_tenencia_by_clasificacion = add_totals(df_tenencia_by_clasificacion, sum_columns=[tenencia_col])
pdf_report.add_df(df_tenencia_by_clasificacion, bold_rows=get_total_rows(df_tenencia_by_clasificacion))

fig_ex = create_grafico_multiple(
    df=df_tenencia_1,
    agg_cols=["asset_class", "issuer_csd_registrar", "denomination_currency"],
    target_col=tenencia_col,
    grid_size=(4, 2),
    plot_positions=[(slice(None), 0), (slice(0, 2), 1), (slice(2, 4), 1)],
    fig_types=['pie', 'pie', 'pie']
)
pdf_report.add_chart(fig_ex)  # Add the chart


pdf_report.add_title("Tenencia - Activo")
df_tenencia_only_assets = df_tenencia_1[df_tenencia_1['Clasificacion']=='Activo']
df_tenencia_by_asset = df_tenencia_only_assets.groupby('Tipo de Instrumento')[tenencia_col].sum().reset_index()
df_tenencia_by_asset = add_totals(df_tenencia_by_asset, sum_columns=[tenencia_col])
pdf_report.add_df(df_tenencia_by_asset, bold_rows=get_total_rows(df_tenencia_by_asset))


pdf_report.add_title("Tenencia - Moneda")
df_tenencia_only_moneda = df_tenencia_1[df_tenencia_1['Clasificacion']=='Moneda']
df_tenencia_by_asset = df_tenencia_only_moneda.groupby('Instrumento - Denominación')[tenencia_col].sum().reset_index()
df_tenencia_by_asset = add_totals(df_tenencia_by_asset, sum_columns=[tenencia_col])
pdf_report.add_df(df_tenencia_by_asset, bold_rows=get_total_rows(df_tenencia_by_asset))


pdf_report.add_title("Tenencia - Todos")
df_tenencia_1_str = df_tenencia_1[['Instrumento - Simbolo', 'Tipo de Instrumento', tenencia_col]]
df_tenencia_1_str = add_subtotals(df_tenencia_1_str, group_by_column='Tipo de Instrumento', sum_columns=[tenencia_col])
pdf_report.add_df(df_tenencia_1_str, bold_rows=get_total_rows(df_tenencia_1_str))


fig_ex = create_grafico_multiple(
    df=df_tenencia_1,
    agg_cols=["Instrumento - Simbolo"],
    target_col=tenencia_col,
    grid_size=(4, 2),
    plot_positions=[(slice(None), slice(None))],
    fig_types=['bar']

)
pdf_report.add_chart(fig_ex)  # Add the chart



pdf_report.build_pdf()

