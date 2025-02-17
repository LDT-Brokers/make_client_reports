import matplotlib.pyplot as plt
from create_pdf.aux_functions import get_colors_from_maps
import pandas as pd
from typing import List, Tuple, Union


def bar_plot(ax, groups, sq_size):
    groups = filter_and_group_otros(groups)
    bars = ax.bar(groups.index, groups.values, color='#425F56', edgecolor='white',
                  linewidth=sq_size)

    # Add percentage labels
    total = groups.sum()
    for bar, value in zip(bars, groups.values):
        percentage = (value / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{percentage:.1f}%', ha='center', va='bottom')

    if len(groups) >= 4:
        plt.xticks(rotation=45, ha='right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    return ax


def zigzag_series(s):
    sorted_s = s.sort_values()
    sorted_desc = sorted_s[::-1].reset_index()
    sorted_asc = sorted_s.reset_index()

    # Interleave largest and smallest while preserving indices
    zigzag = sum(zip(sorted_desc.values, sorted_asc.values), ())[:len(s)]

    return pd.Series([val for _, val in zigzag], index=[idx for idx, _ in zigzag])


def pie_plot(ax, groups, sq_size):
    groups = filter_and_group_otros(groups)
    # zig zag sort
    groups = zigzag_series(groups)
    ax.pie(groups.values, labels=groups.index, labeldistance=1.1, autopct='%1.1f%%', pctdistance=0.8,
           colors=get_colors_from_maps(len(groups)), wedgeprops={'linewidth': sq_size, 'edgecolor': 'white'})
    circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
    ax.add_artist(circle)
    return ax


def filter_and_group_otros(series: pd.Series, t=0.01):
    total_value = series.sum()
    threshold = total_value * t

    filtered_series = series[series > threshold]
    others_value = series[series <= threshold].sum()

    if others_value > t:
        filtered_series = pd.concat([filtered_series, pd.Series({'Otros': others_value})])

    return filtered_series


def create_grafico_multiple(df, agg_cols: List[str], target_col: str, grid_size:Tuple[int, int],
                            plot_positions:List[Tuple[Union[slice, int], Union[slice, int]]], fig_types:List[str]):
    fig = plt.figure(figsize=(10 * grid_size[0], 10 * grid_size[1]))
    sq_size = (grid_size[0] * grid_size[1])
    new_font_size = sq_size * 4
    plt.rcParams.update({'font.size': new_font_size})


    grid = plt.GridSpec(*grid_size)

    for k, agg_col in enumerate(agg_cols):
        groups = df.groupby(agg_col)[target_col].sum().sort_values(ascending=False)

        ax1 = fig.add_subplot(grid[plot_positions[k]])
        if fig_types[k] == 'pie':
            ax1 = pie_plot(ax1, groups, sq_size)
        else:
            ax1 = bar_plot(ax1, groups, sq_size)
        ax1.set_title(f'Distribución de {target_col} por {agg_col}', fontdict={'fontweight': 'bold'})
    plt.tight_layout()
    return fig
