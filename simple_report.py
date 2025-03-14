import pandas as pd
from create_pdf.pdf_report_creator import PDFReport
from create_pdf.aux_functions import  add_subtotals, get_total_rows
from create_pdf.plotting_functions import create_grafico_multiple
from reportlab.lib.colors import HexColor
import sqlite3
from CONFIG import DB_PATH, ASSETS_PATH, OUTPUT_REPORTS_PATH
from datetime import date
from tqdm import tqdm

dt = date.today().strftime("%Y-%m-%d")
today_report_folder = OUTPUT_REPORTS_PATH.joinpath(dt)
today_report_folder.mkdir(parents=True, exist_ok=True)


def query_database(query: str, db_path: str):
    db_conn = sqlite3.connect(db_path)
    with db_conn as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        return df


df_tenencia = query_database(query =f"""
SELECT client_id, g.ticker_norm, precio_prom_compras_no_realizadas, price_usd, asset_class,
       ROUND((price_usd / precio_prom_compras_no_realizadas - 1), 4) * 100 AS rend,
       q_adj_no_realizado * price_usd AS monto
FROM ganancias_summary g
LEFT JOIN all_assets
ON g.code = all_assets.code_caja_val
WHERE q_adj_no_realizado > 0;
""", db_path=DB_PATH)

df_tenencia.rename({'asset_class': 'Clase', 'ticker_norm': 'Especie',
                    'precio_prom_compras_no_realizadas': 'Costo', 'price_usd': 'Precio Mercado', 'rend': 'Retorno [%]',
                    'monto': 'Saldo [USD]'}, axis=1, inplace=True)
df_tenencia = df_tenencia[["client_id", "Clase", "Especie", "Costo", "Precio Mercado", "Retorno [%]", "Saldo [USD]"]].copy()


tc_df = query_database(query =f"""
WITH ccl_ars AS (
    SELECT * from forex_rates where currency_to = 'ARS' AND currency_from = 'USD' AND currency_type = 'CCL'
)
select close, dt from ccl_ars where dt = (select max(dt) from ccl_ars);
""", db_path=DB_PATH)
dt_tc = tc_df.iloc[0,1]
tc = round(tc_df.iloc[0,0], 1)

tenencia_col='Saldo [USD]'

clients_filtered = df_tenencia.groupby('client_id')[tenencia_col].sum()
clients = clients_filtered[clients_filtered >= 20000].index

for selected_client in tqdm(clients):

    df_tenencia_this_client = df_tenencia[df_tenencia.client_id==selected_client].copy()
    df_tenencia_this_client.drop(columns=['client_id'], inplace=True)

    pdf_report = PDFReport(
        filename=today_report_folder.joinpath(f"output_report_{selected_client}.pdf"),
        logo_path=ASSETS_PATH.joinpath("logo-login.png"),
        cover_path=ASSETS_PATH.joinpath("cover.pdf"))

    pdf_report.add_text("Tenencia Total", font_size=24, with_space=False, bold=True)
    pdf_report.add_text(f"USD/ARS: {tc} | {dt_tc}", font_size=14, with_space=False, alignment=2, text_color=HexColor('#70757A'))
    pdf_report.add_divider()

    pdf_report.add_title("Tenencia Total")
    df_tenencia_this_client.sort_values(by=tenencia_col, ascending=False, inplace=True)
    df_tenencia_this_client_wt = add_subtotals(df_tenencia_this_client, group_by_column='Clase', sum_columns=[tenencia_col])
    pdf_report.add_df(df_tenencia_this_client_wt, bold_rows=get_total_rows(df_tenencia_this_client_wt))

    fig_ex = create_grafico_multiple(
        df=df_tenencia_this_client,
        agg_cols=["Clase"],
        target_col=tenencia_col,
        grid_size=(4, 2),
        plot_positions=[(slice(None), slice(None))],
        fig_types=['pie']

    )
    pdf_report.add_chart(fig_ex)



    fig_ex = create_grafico_multiple(
        df=df_tenencia_this_client,
        agg_cols=["Especie"],
        target_col=tenencia_col,
        grid_size=(4, 2),
        plot_positions=[(slice(None), slice(None))],
        fig_types=['bar']

    )
    pdf_report.add_chart(fig_ex)

    pdf_report.build_pdf()

