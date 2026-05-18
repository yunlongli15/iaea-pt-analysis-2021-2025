"""
Analysis 2: Track difficulty changes over years for projects appearing 3+ times.
Identify which projects have significantly changed in difficulty.
Water1/Water2/Water3 variants of the same nuclide-matrix are merged (averaged).
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_all_years
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


def _normalize_core(name):
    """Strip numeric suffixes from matrix names so that Water1/Water2/Water3
    all map to the same base project. E.g. 'Cs-137 Gamma Water1' -> 'Cs-137 Gamma Water'."""
    name = re.sub(r'(Water|Surface|Soil|Sediment|Vegetation)\d+', r'\1', name)
    name = re.sub(r'Alpha\d+', 'Alpha', name)
    name = re.sub(r'Beta\d+', 'Beta', name)
    name = re.sub(r'Gamma\d+', 'Gamma', name)
    return name


def compute_difficulty_series(df):
    """Compute difficulty for each project_core-year combination.
    Difficulty = 1 - N_pass / N_all_labs_in_year (global denominator).
    Pass rate = N_pass / N_labs_in_project (project-specific denominator).
    Water1/Water2/Water3 variants are merged by averaging their difficulty.
    """
    n_all_labs_per_year = df.groupby('year')['labcode'].nunique()

    # Normalize project_core to merge Water1/Water2/etc.
    df = df.copy()
    df['project_base'] = df['project_core'].apply(_normalize_core)

    # Step 1: per file difficulty
    g = df.groupby(['project_core', 'year']).agg(
        n_total=('labcode', 'count'),
        n_pass=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    g['n_all_labs'] = g['year'].map(n_all_labs_per_year)
    g['difficulty'] = 1 - g['n_pass'] / g['n_all_labs']
    g['pass_rate'] = g['n_pass'] / g['n_total']
    g['project_base'] = g['project_core'].apply(_normalize_core)

    # Step 2: merge variants by averaging difficulty and summing counts
    merged = g.groupby(['project_base', 'year']).agg(
        difficulty=('difficulty', 'mean'),
        pass_rate=('pass_rate', 'mean'),
        n_total=('n_total', 'sum'),
        n_pass=('n_pass', 'sum'),
        n_all_labs=('n_all_labs', 'first'),
    ).reset_index()
    merged = merged.rename(columns={'project_base': 'project'})
    return merged


def plot_trending_projects(series, min_years=3, min_diff_change=0.2, save=True):
    """Plot projects with notable difficulty changes."""
    project_years = series.groupby('project')['year'].nunique()
    multi_year = project_years[project_years >= min_years].index
    s = series[series['project'].isin(multi_year)]

    # Compute difficulty range for each project
    ranges = s.groupby('project')['difficulty'].agg(['min', 'max', 'first', 'last'])
    ranges['change'] = ranges['last'] - ranges['first']
    ranges = ranges.sort_values('change')

    # Top increasers (harder over time) and decreasers (easier)
    increasers = ranges.nlargest(8, 'change')
    decreasers = ranges.nsmallest(8, 'change')

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    colors = plt.cm.RdYlGn_r(np.linspace(0.15, 0.85, 8))

    for ax, subset, title in [
        (axes[0], increasers, 'Projects Getting Harder (Difficulty Increasing)'),
        (axes[1], decreasers, 'Projects Getting Easier (Difficulty Decreasing)')
    ]:
        for idx, (proj, row) in enumerate(subset.iterrows()):
            proj_data = s[s['project'] == proj].sort_values('year')
            ax.plot(proj_data['year'], proj_data['difficulty'], 'o-',
                    color=colors[idx], lw=2, markersize=6, label=proj,
                    alpha=0.85)
        ax.set_xlabel('Year')
        ax.set_ylabel('Difficulty Coefficient')
        ax.set_xticks([2021, 2022, 2023, 2024, 2025])
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc='upper left', ncol=2)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_trends.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_trends.pdf'))
    plt.close(fig)


def plot_heatmap(series, min_years=2, save=True):
    """Heatmap of difficulty by project and year."""
    project_years = series.groupby('project')['year'].nunique()
    eligible = project_years[project_years >= min_years].index
    s = series[series['project'].isin(eligible)]

    pivot = s.pivot_table(values='difficulty', index='project', columns='year', aggfunc='mean')

    # Sort by mean difficulty
    pivot['mean'] = pivot.mean(axis=1)
    pivot = pivot.sort_values('mean', ascending=True)
    pivot = pivot.drop(columns='mean')

    fig, ax = plt.subplots(figsize=(10, max(8, len(pivot) * 0.35)))
    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn_r', vmin=0, vmax=1)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(int(c)) for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)

    # Annotate cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=6.5,
                        color='white' if val > 0.6 else 'black')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Difficulty', fontsize=9)

    ax.set_xlabel('Year', fontsize=10)
    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_heatmap.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_heatmap.pdf'))
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_all_years()
    series = compute_difficulty_series(df)

    plot_trending_projects(series)
    plot_heatmap(series)

    # Print projects with biggest changes
    project_years = series.groupby('project')['year'].nunique()
    multi = project_years[project_years >= 3].index
    s = series[series['project'].isin(multi)]
    ranges = s.groupby('project')['difficulty'].agg(['first', 'last', 'min', 'max'])
    ranges['change'] = ranges['last'] - ranges['first']
    ranges = ranges.sort_values('change', ascending=False)

    print('Projects with largest difficulty increases:')
    print(ranges.head(10).to_string())
    print('\nProjects with largest difficulty decreases:')
    print(ranges.tail(10).to_string())

    ranges.to_csv(os.path.join(OUTPUT_DIR, 'difficulty_trends.csv'))


if __name__ == '__main__':
    main()
