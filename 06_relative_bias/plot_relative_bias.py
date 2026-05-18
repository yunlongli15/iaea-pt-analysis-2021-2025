"""
Analysis 6: Relative bias comparison across projects.
Shows our lab's accuracy (relative bias) versus all labs for each project.
Plots exclude |rel_bias| > 100% for visual clarity; statistics use full data.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_all_years, get_our_labcode
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
})


def _strip_prefix(name):
    """Remove leading numeric prefix like '007 - ' from project name."""
    return re.sub(r'^\d+\s*-\s*', '', name)


def _normalize_core(name):
    """Strip numeric suffixes from matrix names (Water1 -> Water, etc.)."""
    name = re.sub(r'(Water|Surface|Soil|Sediment|Vegetation)\d+', r'\1', name)
    name = re.sub(r'Alpha\d+', 'Alpha', name)
    name = re.sub(r'Beta\d+', 'Beta', name)
    name = re.sub(r'Gamma\d+', 'Gamma', name)
    return name


def _add_legend(ax):
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#E91E63',
               markersize=8, label='Our lab'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#90A4AE',
               markersize=6, alpha=0.5, label='Other labs'),
        Line2D([0], [0], marker='|', color='w', markerfacecolor='#333333',
               markersize=8, label='Mean'),
        Line2D([0], [0], color='red', lw=1.2, label='Ref. value (bias=0)'),
    ]
    ax.legend(handles=legend_elements, fontsize=7, loc='upper right')


# ================================================================
# Per-year scatter plot
# ================================================================
def plot_single_year(df, year, save=True):
    lc = get_our_labcode(year)
    dy_all = df[(df['year'] == year) & (df['rel_bias'].notna())]

    # Plot only data within ±100% for visual clarity
    dy = dy_all[dy_all['rel_bias'].abs() <= 100]

    if len(dy) == 0:
        return

    projects = sorted(dy['project'].unique())
    n = len(projects)

    fig, ax = plt.subplots(figsize=(12, max(6, n * 0.26)))

    for i, proj in enumerate(projects):
        pd_data = dy[dy['project'] == proj]
        biases = pd_data['rel_bias'].dropna().values
        our_row = pd_data[pd_data['labcode'] == lc]
        our_bias = our_row['rel_bias'].values[0] if len(our_row) > 0 else np.nan

        jitter = np.random.normal(0, 0.08, len(biases))
        ax.scatter(biases, np.full(len(biases), i) + jitter, alpha=0.4, s=18,
                   color='#90A4AE', edgecolors='none', zorder=2)
        mean_bias = np.mean(biases)
        ax.scatter(mean_bias, i, marker='|', s=100, color='#333333', zorder=4, linewidths=1.5)
        if not np.isnan(our_bias):
            ax.scatter(our_bias, i, s=70, color='#E91E63', marker='D',
                       edgecolors='white', linewidth=1, zorder=5)

    ax.set_yticks(range(n))
    ax.set_yticklabels([_strip_prefix(p) for p in projects], fontsize=7)
    ax.axvline(x=0, color='red', ls='-', lw=1.2, alpha=0.6, zorder=1)
    ax.set_xlabel('Relative Bias [%]')
    ax.set_xlim(-105, 105)
    ax.grid(axis='x', alpha=0.3)
    _add_legend(ax)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, f'relative_bias_{year}.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, f'relative_bias_{year}.pdf'))
    plt.close(fig)


# ================================================================
# Our-lab heatmap — merged by nuclide-matrix, strip prefixes
# ================================================================
def plot_our_lab_summary(df, save=True):
    our_rows = []
    for year in [2021, 2022, 2023, 2024, 2025]:
        lc = get_our_labcode(year)
        dy = df[(df['year'] == year) & (df['labcode'] == lc) & (df['rel_bias'].notna())]
        for _, row in dy.iterrows():
            proj_base = _normalize_core(_strip_prefix(row['project']))
            our_rows.append({
                'year': year,
                'project_base': proj_base,
                'rel_bias': row['rel_bias'],
                'final_score': row['final_score'],
            })
    our_df = pd.DataFrame(our_rows)

    # Merge Water1/Water2 variants by averaging
    merged = our_df.groupby(['project_base', 'year'])['rel_bias'].mean().reset_index()

    pivot = merged.pivot_table(values='rel_bias', index='project_base', columns='year', aggfunc='mean')
    pivot = pivot.loc[pivot.notna().sum(axis=1) >= 2]  # at least 2 years
    pivot['mean_abs'] = pivot.abs().mean(axis=1)
    pivot = pivot.sort_values('mean_abs')
    pivot = pivot.drop(columns='mean_abs')

    fig, ax = plt.subplots(figsize=(10, max(7, len(pivot) * 0.33)))
    vmax = max(pivot.abs().max().max(), 15)
    im = ax.imshow(pivot.values, aspect='auto', cmap=plt.cm.RdBu_r, vmin=-vmax, vmax=vmax)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = 'white' if abs(val) > vmax * 0.6 else 'black'
                ax.text(j, i, f'{val:.1f}', ha='center', va='center', fontsize=7,
                        color=text_color, fontweight='bold')

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(int(c)) for c in pivot.columns], fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.set_xlabel('Year')
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Relative Bias [%]', fontsize=9)
    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'our_relative_bias_heatmap.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'our_relative_bias_heatmap.pdf'))
    plt.close(fig)


# ================================================================
# Ranking bar chart — all years, stripped prefixes
# ================================================================
def plot_ranking_summary(df, year, save=True):
    lc = get_our_labcode(year)
    dy = df[(df['year'] == year) & (df['rel_bias'].notna())]

    results = []
    for proj, group in dy.groupby('project'):
        group = group.copy()
        group['abs_bias'] = group['rel_bias'].abs()
        n_total = len(group)
        if lc not in group['labcode'].values:
            continue
        our_abs = group[group['labcode'] == lc]['abs_bias'].values[0]
        our_rel = group[group['labcode'] == lc]['rel_bias'].values[0]
        rank = (group['abs_bias'] < our_abs).sum() + 1
        results.append({
            'project': _strip_prefix(proj),
            'n_total': n_total,
            'our_abs_bias': our_abs,
            'our_rel_bias': our_rel,
            'our_rank': rank,
            'our_percentile': rank / n_total * 100,
        })

    rdf = pd.DataFrame(results).sort_values('our_percentile')
    n = len(rdf)

    fig, ax = plt.subplots(figsize=(10, max(6, n * 0.28)))
    cmap = plt.cm.RdYlGn
    norm = plt.Normalize(0, 100)
    colors = cmap(norm(rdf['our_percentile'].values))
    ax.barh(np.arange(n), rdf['our_percentile'].values, color=colors, alpha=0.85, zorder=3)

    for i, (_, row) in enumerate(rdf.iterrows()):
        ax.text(row['our_percentile'] + 1, i,
                f'#{int(row["our_rank"])}/{int(row["n_total"])} (|bias|={row["our_abs_bias"]:.1f}%)',
                va='center', fontsize=6.5)

    ax.set_yticks(np.arange(n))
    ax.set_yticklabels(rdf['project'].values, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel('Percentile Rank (%)  —  lower = better')
    ax.set_xlim(0, 105)
    ax.axvline(x=50, color='red', ls='--', lw=1, alpha=0.5, label='Median')
    ax.grid(axis='x', alpha=0.3)
    ax.legend(fontsize=7)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
    cbar.set_label('Percentile', fontsize=7)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, f'ranking_{year}.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, f'ranking_{year}.pdf'))
    plt.close(fig)

    rdf.to_csv(os.path.join(OUTPUT_DIR, f'ranking_{year}.csv'), index=False)
    return rdf


# ================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_all_years()

    for year in [2021, 2022, 2023, 2024, 2025]:
        plot_single_year(df, year)
        print(f'{year} relative bias plot done.')

    plot_our_lab_summary(df)

    for year in [2021, 2022, 2023, 2024, 2025]:
        rdf = plot_ranking_summary(df, year)
        print(f'\n{year} ranking summary:')
        print(f'  Mean percentile: {rdf["our_percentile"].mean():.1f}%')
        print(f'  Median percentile: {rdf["our_percentile"].median():.1f}%')
        print(f'  Best: #{int(rdf["our_rank"].min())} in {rdf.loc[rdf["our_rank"].idxmin(), "project"]}')
        print(f'  Worst: #{int(rdf["our_rank"].max())} in {rdf.loc[rdf["our_rank"].idxmax(), "project"]}')


if __name__ == '__main__':
    main()
