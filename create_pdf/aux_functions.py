from PyPDF2 import PdfMerger
from matplotlib.colors import LinearSegmentedColormap
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
    if n == 1:
        colors = [cmap(0.5)]  # Pick the midpoint color
    else:
        colors = [cmap(i / (n-1)) for i in range(n)]  # Evenly spaced
    return colors

def merge_pdfs(pdf1, pdf2, output_pdf):
    merger = PdfMerger()

    merger.append(pdf1)
    merger.append(pdf2)

    merger.write(output_pdf)
    merger.close()

def add_totals(df, sum_columns=None):
    sum_columns = sum_columns if sum_columns is not None else df.select_dtypes(include=['number']).columns
    df = df.copy()
    df['grouper_col'] = 1
    df = add_subtotals(df, 'grouper_col', sum_columns)
    df.iloc[:, 0] = df.apply(lambda row: "Total" if row['grouper_col'] != 1 else row.iloc[0], axis=1)
    df.drop('grouper_col', axis=1, inplace=True)
    return df

def add_subtotals(df, group_by_column, sum_columns= None):
    sum_columns = sum_columns if sum_columns is not None else df.select_dtypes(include=['number']).columns
    df = df.copy()
    subtotal_df = df.groupby(group_by_column)[sum_columns].sum().reset_index()
    subtotal_df[group_by_column] = subtotal_df[group_by_column].astype(str) + ' (Total)'
    df_with_subtotals = pd.concat([df, subtotal_df], ignore_index=True)
    df_with_subtotals.sort_values(inplace=True, by=[group_by_column, *sum_columns], ascending=[True] + [False] * len(sum_columns))
    if len(sum_columns) == 1:
        df_with_subtotals['Part [%]'] = df_with_subtotals[sum_columns] / df_with_subtotals[sum_columns].sum()* 100 * 2 # add *2 because we are double counting the the total
    return df_with_subtotals


def get_total_rows(df, col=None):
    if col is None:
        col = df.columns[0]  # Default to the first column
    return list(np.where(df[col].astype(str).fillna('').str.contains('Total'))[0])