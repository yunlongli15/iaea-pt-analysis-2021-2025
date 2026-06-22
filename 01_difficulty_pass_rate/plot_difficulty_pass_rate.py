"""
Analysis 1: Difficulty coefficient and pass rate for each project, by year.
Difficulty = 1 - N_satisfactory / N_all_labs_in_year
Pass rate = N_satisfactory / N_labs_in_this_project
The two metrics have DIFFERENT denominators and are NOT complementary.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_year
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import re

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

YEAR_COLORS = {2021: '#1f77b4', 2022: '#ff7f0e', 2023: '#2ca02c',
               2024: '#d62728', 2025: '#9467bd'}

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
})


def strip_prefix(name):
    """Remove leading numeric prefix like '001 - ' from project name."""
    return re.sub(r'^\d+\s*-\s*', '', name)


def compute_project_stats(df):
    """Compute difficulty and pass rate for each project.
    Difficulty uses ALL unique labs in the year as denominator.
    Pass rate uses only labs that participated in this specific project.
    """
    n_all_labs = df['labcode'].nunique()

    stats = df.groupby('project').agg(
        n_total=('labcode', 'count'),
        n_pass=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    stats['difficulty'] = 1 - stats['n_pass'] / n_all_labs
    stats['pass_rate'] = stats['n_pass'] / stats['n_total']
    stats = stats.sort_values('difficulty', ascending=True)
    return stats


def plot_year(stats, year, save=True):
    """Horizontal bar chart (difficulty) + overlaid line plot (pass rate).
    Dual x-axes: bottom = difficulty, top = pass rate."""
    stats = stats.sort_values('difficulty', ascending=True)
    n = len(stats)

    fig, ax1 = plt.subplots(figsize=(10, max(6, n * 0.32)))

    y_pos = np.arange(n)

    # --- Bottom axis: Difficulty (bar chart) ---
    bar_color = '#78909C'   # blue-grey
    ax1.barh(y_pos, stats['difficulty'].values, height=0.6,
             color=bar_color, alpha=0.80, zorder=2, label='Difficulty')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([strip_prefix(p) for p in stats['project'].values], fontsize=8)
    ax1.set_xlabel('Difficulty Coefficient', fontsize=10, color='#455A64')
    ax1.set_xlim(0, 1.05)
    ax1.invert_yaxis()
    ax1.tick_params(axis='x', colors='#455A64')

    # --- Top axis: Pass Rate (line + scatter) ---
    ax2 = ax1.twiny()
    line_color = '#FF6D00'  # deep orange
    ax2.plot(stats['pass_rate'].values, y_pos, 'D-', color=line_color,
             lw=1.8, markersize=5, markerfacecolor=line_color, markeredgewidth=0.5,
             markeredgecolor='white', zorder=4, label='Pass Rate')
    ax2.set_xlabel('Pass Rate', fontsize=10, color=line_color)
    ax2.set_xlim(0, 1.05)
    ax2.tick_params(axis='x', colors=line_color)

    # Value annotations on the line markers
    for i, pr in enumerate(stats['pass_rate'].values):
        ax2.annotate(f'{pr:.2f}', (pr, i), textcoords="offset points",
                     xytext=(10, -1), ha='left', va='center', fontsize=6, color=line_color)

    # --- Legend ---
    from matplotlib.lines import Line2D
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, fc=bar_color, alpha=0.80, label='Difficulty'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor=line_color,
               markersize=6, lw=1.8, markeredgecolor='white', label='Pass Rate'),
    ]
    ax1.legend(handles=legend_elements, fontsize=7, loc='lower right',
               framealpha=0.9, edgecolor='#ccc')

    ax1.grid(axis='x', alpha=0.25, zorder=0)
    ax1.text(0.98, 0.02, f'{n} projects', transform=ax1.transAxes, ha='right',
             fontsize=7, color='gray')

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, f'difficulty_pass_rate_{year}.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, f'difficulty_pass_rate_{year}.pdf'))
    plt.close(fig)


def plot_all_years_overview(yearly_data, save=True):
    """Combined overview: difficulty distribution per year as boxplot + scatter."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Boxplot with jittered project points
    ax = axes[0]
    years = sorted(yearly_data.keys())
    data = [yearly_data[y]['difficulty'].values for y in years]
    bp = ax.boxplot(data, tick_labels=[str(y) for y in years], patch_artist=True,
                    widths=0.5, zorder=2)
    for patch, y in zip(bp['boxes'], years):
        patch.set_facecolor(YEAR_COLORS.get(y, '#cccccc'))
        patch.set_alpha(0.45)
    # Jittered individual project points
    for i, y in enumerate(years):
        vals = data[i]
        if len(vals) > 0:
            jitter = np.random.normal(0, 0.06, len(vals))
            ax.scatter(np.full(len(vals), i + 1) + jitter, vals, alpha=0.55, s=22,
                       color=YEAR_COLORS.get(y, '#333'), edgecolors='white',
                       linewidth=0.3, zorder=4)
    # Annotate mean + count per year
    for i, y in enumerate(years):
        vals = data[i]
        mean_val = np.mean(vals)
        ax.annotate(f'mean={mean_val:.3f}\nn={len(vals)}',
                    (i + 1 + 0.25, mean_val), textcoords="offset points",
                    xytext=(6, 0), ha='left', va='center', fontsize=7,
                    color='#333')
    ax.set_ylabel('Difficulty Coefficient')
    ax.set_ylim(-0.05, 1.1)
    ax.grid(axis='y', alpha=0.3)

    # Mean difficulty trend
    ax = axes[1]
    means = [yearly_data[y]['difficulty'].mean() for y in years]
    stds = [yearly_data[y]['difficulty'].std() for y in years]
    ax.errorbar(years, means, yerr=stds, fmt='o-', capsize=5, capthick=1.5,
                lw=2, markersize=8, color='#333333', zorder=3)
    ax.set_ylabel('Mean Difficulty Coefficient')
    ax.set_xticks(years)
    ax.set_ylim(0, max(0.7, max(means) + max(stds) + 0.1))
    ax.grid(axis='y', alpha=0.3)
    for yr, m in zip(years, means):
        ax.annotate(f'{m:.3f}', (yr, m), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=8)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_overview.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_overview.pdf'))
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    yearly_data = {}
    for year in [2021, 2022, 2023, 2024, 2025]:
        df = load_year(year)
        stats = compute_project_stats(df)
        yearly_data[year] = stats
        plot_year(stats, year)
        print(f'{year}: {len(stats)} projects, mean difficulty={stats["difficulty"].mean():.3f}')

    plot_all_years_overview(yearly_data)

    # Summary table
    rows = []
    for year, stats in yearly_data.items():
        rows.append({
            'Year': year,
            'Projects': len(stats),
            'Mean Difficulty': f'{stats["difficulty"].mean():.3f}',
            'Median Difficulty': f'{stats["difficulty"].median():.3f}',
            'Max Difficulty': f'{stats["difficulty"].max():.3f}',
            'Mean Pass Rate': f'{stats["pass_rate"].mean():.3f}',
            'Pass rate >0.9': f'{(stats["pass_rate"] > 0.9).sum()}',
            'Pass rate =1.0': f'{(stats["pass_rate"] == 1.0).sum()}',
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, 'difficulty_summary.csv'), index=False)
    print('\nSummary saved.')
    print(summary.to_string())


if __name__ == '__main__':
    main()
