from PyPDF2 import PdfMerger
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_cmap(groups):
    if groups < 5:
        cmap = LinearSegmentedColormap.from_list("custom_GrGr", ['#425F56', '#BBC3C1'], N=groups)
    elif groups < 10:
        cmap = LinearSegmentedColormap.from_list("custom_YlGrGr", ['#D4A373', '#425F56', '#BBC3C1'], N=groups)
    else:
        cmap = LinearSegmentedColormap.from_list("custom_ReYlGrGr", ['#A16569', '#D4A373','#425F56', '#BBC3C1'], N=groups)
    return cmap

def get_colors_from_maps(n):
    cmap = get_cmap(n)
    colors = [cmap(i / (n - 1)) for i in range(n)]  # Evenly spaced
    return colors

def merge_pdfs(pdf1, pdf2, output_pdf):
    merger = PdfMerger()

    merger.append(pdf1)
    merger.append(pdf2)

    merger.write(output_pdf)
    merger.close()

def crear_grafico(df, agg_col, target_col):
    groups = df.groupby(agg_col)[target_col].sum()
    fig, ax = plt.subplots(figsize=(6, 6))
    num_groups = len(groups)

    ax.pie(groups, labels=groups.index, autopct='%1.1f%%', colors=get_colors_from_maps(num_groups))
    ax.set_title(f'Distribución de {target_col} por {agg_col}')
    return fig


def add_totals(df):
    first_col = df.columns[0]
    total_values = df.select_dtypes(include='number').sum().to_dict()
    total_row = {col: total_values.get(col, None) for col in df.columns}
    total_row[first_col] = 'Total'
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    return df

def add_subtotals(df, group_by_column, sum_columns=None):
    if sum_columns is None:
        sum_columns = df.select_dtypes(include='number').columns.tolist()
    subtotal_df = df.groupby(group_by_column)[sum_columns].sum().reset_index()
    subtotal_df[group_by_column] = subtotal_df[group_by_column].astype(str) + ' (Total)'
    df_with_subtotals = pd.concat([df, subtotal_df], ignore_index=True)
    df_with_subtotals = df_with_subtotals.sort_values(by=[group_by_column], ascending=True)
    if df_with_subtotals.columns[0] != group_by_column:
        df_with_subtotals.iloc[:, 0] = df_with_subtotals.apply(
            lambda row: "Total" if "Total" in str(row[group_by_column]) else row.iloc[0], axis=1
        )
    return df_with_subtotals


def get_total_rows(df, col=None):
    if col is None:
        return list(np.where(df.iloc[:, 0].str.contains('Total'))[0])
    else:
        return list(np.where(df[col].str.contains('Total'))[0])
