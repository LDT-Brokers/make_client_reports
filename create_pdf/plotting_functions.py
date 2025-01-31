import matplotlib.pyplot as plt
from create_pdf.aux_functions import get_colors_from_maps
import numpy as np
import pandas as pd
import matplotlib

def bar_plot(ax, groups, sq_size):
    groups = groups.sort_values(ascending=False).head(20)
    ax.bar(groups.index, groups.values, color='#425F56', edgecolor='white',
            linewidth=sq_size)
    plt.xticks(rotation=45, ha='right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    return ax

def pie_plot(ax, groups, sq_size):
    groups = top_n_with_others(groups, n=20)
    ax.pie(groups.values, labels=groups.index, labeldistance=1.1, autopct='%1.1f%%', pctdistance=0.8,
            colors=get_colors_from_maps(len(groups)), wedgeprops={'linewidth': sq_size, 'edgecolor': 'white'})
    circle = plt.Circle(xy=(0, 0), radius=0.5, facecolor='white')
    ax.add_artist(circle)
    return ax

def top_n_with_others(s, n):
    if len(s) >= n:
        s.sort_values(inplace=True, ascending=False)
        top_n = s.head(n)  # Get top n values
        others_sum = s.iloc[n:].sum()  # Sum the rest
        top_n["Otros"] = others_sum  # Add 'Otros' category
        return top_n
    else:
        return s

def create_grafico_multiple(df, agg_cols, target_col, grid_size, plot_positions, fig_types):
    fig = plt.figure(figsize=(10 * grid_size[0], 10 * grid_size[1]))
    sq_size = (grid_size[0] * grid_size[1])
    new_font_size = sq_size * 4
    matplotlib.rcParams.update({'font.size': new_font_size})

    grid = plt.GridSpec(*grid_size)

    for k, agg_col in enumerate(agg_cols):
        groups = df.groupby(agg_col)[target_col].sum().sort_values(ascending=False)

        ax1 = plt.subplot(grid[plot_positions[k]])
        if fig_types[k] == 'pie':
            ax1 = pie_plot(ax1, groups, sq_size)
        else:
            ax1 = bar_plot(ax1, groups, sq_size)
        ax1.set_title(f'Distribución de {target_col} por {agg_col}', fontdict={'fontweight': 'bold'})
    plt.tight_layout()
    return fig

if __name__ == '__main__':
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

    create_grafico_multiple(
        df=df_assets,
        agg_cols=["Tipo de Activo", "Local o Extranjera", "Fija o Variable"],
        target_col="Tenencia",
        grid_size= (4, 2),
        plot_positions=[(slice(None), 0), (slice(0,2), 1), (slice(2,4), 1)],
        fig_types=['pie', 'bar', 'bar']
    )

    create_grafico_multiple(
        df=df_assets,
        agg_cols=["Tipo de Activo", "Local o Extranjera", "Fija o Variable"],
        target_col="Tenencia",
        grid_size= (4, 2),
        plot_positions=[(0, 0), (0, 1), (1, slice(None))],
        fig_types=['pie', 'bar', 'bar']
    )

