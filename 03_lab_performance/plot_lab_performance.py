"""
Analysis 3: Lab performance scatter plots — per year.
Y-axis: number of projects participated / passed per lab.
X-axis: lab codes, sorted by participation count descending.
Our lab highlighted in red.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_year, get_our_labcode
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
YEAR_COLORS = {2021: '#1f77b4', 2022: '#ff7f0e', 2023: '#2ca02c',
               2024: '#d62728', 2025: '#9467bd'}

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
})


def plot_year_scatter(df, year, save=True):
    """Scatter plot: each lab's participated and passed project counts."""
    lc_our = get_our_labcode(year)
    dy = df[df['year'] == year]

    # Per-lab stats
    stats = dy.groupby('labcode').agg(
        n_participated=('project', 'nunique'),
        n_passed=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    stats = stats.sort_values('n_participated', ascending=False).reset_index(drop=True)

    # Tied ranking: labs with same participation count share the same rank
    stats['rank'] = stats['n_participated'].rank(method='min', ascending=False).astype(int)
    stats['rank_A'] = stats['n_passed'].rank(method='min', ascending=False).astype(int)
    n_labs = len(stats)

    fig, ax = plt.subplots(figsize=(max(12, n_labs * 0.06), 6))

    x = np.arange(n_labs)

    # Participated (circle)
    participated_mask = stats['labcode'] != lc_our
    ax.scatter(x[participated_mask], stats.loc[participated_mask, 'n_participated'],
               s=40, color=YEAR_COLORS.get(year, '#999'), alpha=0.6,
               label='Participated (other labs)', zorder=3)

    # Passed (triangle)
    ax.scatter(x[participated_mask], stats.loc[participated_mask, 'n_passed'],
               s=40, marker='^', color=YEAR_COLORS.get(year, '#999'), alpha=0.5,
               label='Passed (A) (other labs)', zorder=3)

    # Our lab - highlighted (smaller markers than before)
    our_mask = stats['labcode'] == lc_our
    if our_mask.any():
        our_idx = np.where(our_mask)[0][0]
        our_row = stats[our_mask].iloc[0]
        ax.scatter(our_idx, our_row['n_participated'], s=90, color='#E91E63',
                   edgecolors='black', linewidth=1.0, zorder=5,
                   label=f'Our lab ({lc_our}) - Participated')
        ax.scatter(our_idx, our_row['n_passed'], s=90, marker='^', color='#FF5722',
                   edgecolors='black', linewidth=1.0, zorder=5,
                   label=f'Our lab ({lc_our}) - Passed')
        ax.annotate(f'P#{int(our_row["rank"])} / A#{int(our_row["rank_A"])}\nP:{int(our_row["n_participated"])} A:{int(our_row["n_passed"])}',
                    (our_idx, our_row['n_participated']),
                    textcoords="offset points", xytext=(0, 18), ha='center',
                    fontsize=8, fontweight='bold', color='#E91E63')

    # X-axis: show lab codes only when not too many, otherwise selective
    if n_labs <= 80:
        ax.set_xticks(x)
        ax.set_xticklabels(stats['labcode'].astype(str), fontsize=5, rotation=90)
    else:
        step = max(1, n_labs // 50)
        tick_idx = x[::step]
        ax.set_xticks(tick_idx)
        ax.set_xticklabels(stats.loc[stats['rank'] - 1 - tick_idx[0] == np.arange(len(tick_idx)) * step - tick_idx[0],
                                     'labcode'].astype(str) if False else stats.iloc[::step]['labcode'].astype(str),
                          fontsize=5, rotation=90)

    ax.set_ylabel('Number of Projects', fontsize=11)
    ax.set_xlabel('Laboratory (sorted by participation)', fontsize=10)
    ax.legend(fontsize=6, loc='upper right', markerscale=0.7, handletextpad=0.3,
              borderpad=0.3, labelspacing=0.2)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, f'lab_performance_{year}.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, f'lab_performance_{year}.pdf'))
    plt.close(fig)
    return stats


def plot_comparison(yearly_stats, save=True):
    """Multi-year comparison: our lab's participation & rank across years."""
    years = sorted(yearly_stats.keys())

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: bar chart of our participation
    ax = axes[0]
    our_parts = []
    our_passes = []
    our_ranks = []
    total_labs_list = []
    for y in years:
        stats = yearly_stats[y]
        lc = get_our_labcode(y)
        our = stats[stats['labcode'] == lc]
        if len(our) > 0:
            our_parts.append(our['n_participated'].values[0])
            our_passes.append(our['n_passed'].values[0])
            our_ranks.append(our['rank'].values[0])
            total_labs_list.append(len(stats))
        else:
            our_parts.append(0)
            our_passes.append(0)
            our_ranks.append(None)
            total_labs_list.append(len(stats))

    x = np.arange(len(years))
    w = 0.35
    bar_centers = x - w/2
    ax.bar(bar_centers, our_parts, w, color='#2196F3', label='Participated', zorder=3)
    ax.bar(bar_centers, our_passes, w/2, color='#4CAF50', label='Passed (A)', zorder=4)
    for xc, p in zip(bar_centers, our_parts):
        ax.text(xc, p + 0.5, str(p), ha='center', fontsize=9, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_ylabel('Number of Projects')
    ax.legend(fontsize=6, markerscale=0.7, handletextpad=0.3,
              borderpad=0.3)
    ax.grid(axis='y', alpha=0.3)

    # Right: our rank over years (participation + A-count)
    ax = axes[1]
    our_A_ranks = []
    for y in years:
        stats = yearly_stats[y]
        lc = get_our_labcode(y)
        our = stats[stats['labcode'] == lc]
        if len(our) > 0:
            our_A_ranks.append(our['rank_A'].values[0])
        else:
            our_A_ranks.append(None)

    ax.plot(years, our_ranks, 'o-', color='#2196F3', lw=2.5, markersize=9, zorder=3,
            label='By participation')
    ax.plot(years, our_A_ranks, 's--', color='#4CAF50', lw=2.5, markersize=9, zorder=3,
            label='By A scores')
    ax.set_xticks(years)
    ax.set_ylabel('Global Rank', fontsize=10)
    ax.invert_yaxis()
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc='lower right')
    for y, r, a, t in zip(years, our_ranks, our_A_ranks, total_labs_list):
        # Annotate participation rank point
        ax.annotate(f'P#{r}', (y, r),
                    textcoords="offset points", xytext=(8, 6), ha='left', va='bottom',
                    fontsize=7, fontweight='bold', color='#2196F3')
        # Annotate A-count rank point
        ax.annotate(f'A#{a}', (y, a),
                    textcoords="offset points", xytext=(8, -6), ha='left', va='top',
                    fontsize=7, fontweight='bold', color='#4CAF50')
    # Note total labs
    ax.text(0.02, 0.02, f'Total labs range: {min(total_labs_list)}–{max(total_labs_list)}',
            transform=ax.transAxes, fontsize=6, color='gray')

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'lab_performance.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'lab_performance.pdf'))
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    yearly_stats = {}

    # Per-year scatter plots
    for year in [2021, 2022, 2023, 2024, 2025]:
        print(f'Loading {year}...')
        df = load_year(year)
        stats = plot_year_scatter(df, year)
        yearly_stats[year] = stats

        lc = get_our_labcode(year)
        our = stats[stats['labcode'] == lc]
        if len(our) > 0:
            r = our.iloc[0]
            total_proj = df['project'].nunique()
            print(f'  {year}: {len(stats)} labs, {total_proj} projects | '
                  f'Our lab ({lc}): P#{int(r["rank"])}/A#{int(r["rank_A"])}, '
                  f'{int(r["n_participated"])} participated, {int(r["n_passed"])} passed (A)')

    # Multi-year comparison
    plot_comparison(yearly_stats)

    # Percentile ranking (keep existing functionality)
    from data_loader import load_all_years
    all_df = load_all_years()

    all_rankings = []
    for year in [2021, 2022, 2023, 2024, 2025]:
        lc = get_our_labcode(year)
        dy = all_df[all_df['year'] == year].dropna(subset=['rel_bias'])
        for proj, group in dy.groupby('project'):
            group = group.copy()
            group['abs_bias'] = group['rel_bias'].abs()
            n_total = len(group)
            if lc not in group['labcode'].values:
                continue
            our_bias = group[group['labcode'] == lc]['abs_bias'].values[0]
            our_rank = (group['abs_bias'] < our_bias).sum() + 1
            our_final = group[group['labcode'] == lc]['final_score'].values[0]
            all_rankings.append({
                'year': year, 'project': proj, 'n_total': n_total,
                'our_rank': our_rank, 'our_percentile': our_rank / n_total * 100,
                'our_final': our_final,
            })

    rankings_df = pd.DataFrame(all_rankings)
    rankings_df.to_csv(os.path.join(OUTPUT_DIR, 'lab_rankings_detail.csv'), index=False)

    # Boxplot: our percentile distribution by year + jittered project points
    fig, ax = plt.subplots(figsize=(9, 5.5))
    years = [2021, 2022, 2023, 2024, 2025]
    data_by_year = []
    positions_by_year = []
    for y in years:
        ry = rankings_df[rankings_df['year'] == y]
        data_by_year.append(ry['our_percentile'].values)
        positions_by_year.append(y)

    bp = ax.boxplot(data_by_year, tick_labels=[str(y) for y in years],
                    patch_artist=True, widths=0.45, zorder=2)
    for patch, y in zip(bp['boxes'], years):
        patch.set_facecolor(YEAR_COLORS.get(y, '#cccccc'))
        patch.set_alpha(0.55)

    # Jittered individual project points
    for i, y in enumerate(years):
        vals = data_by_year[i]
        if len(vals) > 0:
            jitter = np.random.normal(0, 0.06, len(vals))
            ax.scatter(np.full(len(vals), i + 1) + jitter, vals, alpha=0.55, s=22,
                       color=YEAR_COLORS.get(y, '#333'), edgecolors='white',
                       linewidth=0.3, zorder=4)

    # Annotate mean + count per year
    for i, y in enumerate(years):
        vals = data_by_year[i]
        if len(vals) > 0:
            mean_val = np.mean(vals)
            ax.annotate(f'mean={mean_val:.1f}%\nn={len(vals)}',
                        (i + 1, mean_val), textcoords="offset points",
                        xytext=(12, 0), ha='left', va='center', fontsize=7,
                        color='#333')

    ax.axhline(y=50, color='#E91E63', ls='--', lw=1.2, alpha=0.7, label='Median (50%)')
    ax.set_ylabel('Our Percentile Rank (%)  —  lower = better')
    ax.set_xlabel('Year')
    ax.set_ylim(105, -5)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'lab_percentile_ranking.png'))
    fig.savefig(os.path.join(OUTPUT_DIR, 'lab_percentile_ranking.pdf'))
    plt.close(fig)

    print(f'\nPercentile rankings saved. Mean: {rankings_df["our_percentile"].mean():.1f}%')


if __name__ == '__main__':
    main()
