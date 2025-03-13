import pandas as pd
from create_pdf.pdf_report_creator import PDFReport
from create_pdf.aux_functions import  add_subtotals, add_totals, get_total_rows
from create_pdf.plotting_functions import create_grafico_multiple, get_basic_grid_pos
from reportlab.lib.colors import HexColor
from CONFIG import DB_PATH, ASSETS_PATH, OUTPUT_REPORTS_PATH
from datetime import date
from tqdm import tqdm
import sqlite_utils
import matplotlib.pyplot as plt


dt = date.today().strftime("%Y-%m-%d")
today_report_folder = OUTPUT_REPORTS_PATH.joinpath(dt)
today_report_folder.mkdir(parents=True, exist_ok=True)

db = sqlite_utils.Database(DB_PATH)
def query_database(query):
    return pd.DataFrame(db.query(query))


df_tenencia = query_database("""
SELECT client_id, g.ticker_norm, precio_prom_compras_no_realizadas, price_usd, asset_class,
       ROUND((price_usd / precio_prom_compras_no_realizadas - 1), 4) * 100 AS rend,
       q_adj_no_realizado * price_usd AS monto,
       all_assets.sector, all_assets.industry_group, all_assets.issuer, all_assets.long_name_es,
        SUBSTR(code_isin, 1,2) AS country
FROM ganancias_summary g
LEFT JOIN all_assets
ON g.code = all_assets.code_caja_val
WHERE q_adj_no_realizado > 0;
""")


df_tenencia = query_database("""
SELECT client_id, g.ticker_norm, precio_prom_compras_no_realizadas, price_usd, asset_class,
       ROUND((price_usd / precio_prom_compras_no_realizadas - 1), 4) * 100 AS rend,
       q_adj_no_realizado * price_usd AS monto,
       all_assets.sector, all_assets.industry_group, all_assets.issuer, all_assets.long_name_es,
        SUBSTR(code_isin, 1,2) AS country
FROM ganancias_summary g
LEFT JOIN all_assets
ON g.code = all_assets.code_caja_val
WHERE q_adj_no_realizado > 0 and client_id=23012;
""")


df_tenencia.rename({'asset_class': 'Clase', 'ticker_norm': 'Especie',
                    'precio_prom_compras_no_realizadas': 'Costo', 'price_usd': 'Precio Mercado', 'rend': 'Retorno [%]',
                    'monto': 'Saldo [USD]'}, axis=1, inplace=True)
# df_tenencia = df_tenencia[["client_id", "Clase", "Especie", "Costo", "Precio Mercado", "Retorno [%]", "Saldo [USD]"]].copy()


tc_df = query_database("""
    SELECT close, dt FROM forex_rates 
    WHERE currency_to = 'ARS' AND currency_from = 'USD' AND currency_type = 'CCL' 
    ORDER BY dt DESC LIMIT 1
""")
dt_tc = tc_df.iloc[0, 1]

tc = round(tc_df.iloc[0,0], 1)



class ReporteCompleto:
    def __init__(self, df_tenencia_in):
        self.pdf_report = PDFReport(
            filename=today_report_folder.joinpath(f"output_report_{selected_client}.pdf"),
            logo_path=ASSETS_PATH.joinpath("logo-login.png"),
            cover_path=ASSETS_PATH.joinpath("cover.pdf"))
        self.df_tenencia = df_tenencia_in
        self.tenencia_col='Saldo [USD]'

    def page_intro(self):
        self.pdf_report.add_text("Resumen de Tenencia", font_size=24, with_space=False, bold=True)
        self.pdf_report.add_text(f"USD/ARS: {tc} | {dt_tc}", font_size=14, with_space=False, alignment=2,
                                 text_color=HexColor('#70757A'))
        self.pdf_report.add_divider()

    def p_resumen_activos(self):
        self.pdf_report.add_title("Tenencia Total")
        df = self.df_tenencia.groupby('Clase')[self.tenencia_col].sum().reset_index()
        df = add_totals(df[['Clase', self.tenencia_col]])
        self.pdf_report.add_df(df, bold_rows=get_total_rows(df))

        fig_ex = create_grafico_multiple(
            df=self.df_tenencia,
            agg_cols=["Clase", "country", "sector"],
            target_col=self.tenencia_col,
            grid_size=(4,2),
            plot_positions=[(slice(None), slice(0,-1)), (slice(0,2), -1), (slice(2,4), -1)],
            fig_types=['pie', 'pie', 'pie']

        )
        self.pdf_report.add_chart(fig_ex)

    def p_by_asset_type(self, asset_type, relevant_cols):
        df = self.df_tenencia[self.df_tenencia['Clase'] == asset_type].copy()
        if df.empty:
            return

        self.pdf_report.add_title(asset_type)
        df_disp = add_totals(df[relevant_cols])
        self.pdf_report.add_df(df_disp, bold_rows=get_total_rows(df_disp), col_widths=[14,7,14,14,10,5])

        agg_cols = relevant_cols[:-1]
        gs, pp = get_basic_grid_pos(len(agg_cols))

        fig = create_grafico_multiple(
            df=df,
            agg_cols=agg_cols,
            target_col=self.tenencia_col,
            grid_size=gs,
            plot_positions=pp,
            fig_types=['pie'] * len(agg_cols)

        )
        self.pdf_report.add_chart(fig)

    def new_section(self, section_name):
        self.pdf_report.new_page()
        self.pdf_report.add_text(section_name, font_size=24, with_space=False, bold=True)
        self.pdf_report.add_divider()

    def p_precios(self):
        df = self.df_tenencia.sort_values(by=self.tenencia_col, ascending=False).copy()
        df_disp = add_subtotals(df, group_by_column='Clase', sum_columns=[self.tenencia_col])
        df_disp = df_disp[["Clase", "Especie", "Costo", "Precio Mercado", "Retorno [%]", "Saldo [USD]"]].copy()
        self.pdf_report.add_df(df_disp, bold_rows=get_total_rows(df_disp))

        fig = create_grafico_multiple(
            df=df,
            agg_cols=["Especie"],
            target_col=self.tenencia_col,
            grid_size=(4, 2),
            plot_positions=[(slice(None), slice(None))],
            fig_types=['bar']

        )
        self.pdf_report.add_chart(fig)

    def run(self):
        self.page_intro()
        self.p_resumen_activos()

        self.new_section("Todos los Activos Ganancia")
        self.p_precios()

        self.new_section("Desglose por Tipo de Activo")
        for k, asset_class in enumerate(self.df_tenencia['Clase'].unique()):
            if k > 0:
                self.pdf_report.new_page()
            self.p_by_asset_type(asset_type=asset_class,
                                 relevant_cols=['issuer', 'country', 'industry_group', 'sector', self.tenencia_col])




        self.pdf_report.build_pdf()


clients = [23012]

for selected_client in tqdm(clients):

    df_tenencia_this_client = df_tenencia[df_tenencia.client_id==selected_client].copy()
    df_tenencia_this_client = df_tenencia_this_client[~df_tenencia_this_client['Saldo [USD]'].isnull()]
    reporte = ReporteCompleto(df_tenencia_this_client)
    reporte.run()
    plt.close('all')

