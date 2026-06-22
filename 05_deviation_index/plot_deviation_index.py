"""
Analysis 5: Result Deviation Index (RDI) scatter plots — per year.

Weighted RDI = (1/K) * sum |rel_bias_k| * w_k
where w_k = 1.2 / (1 + MARB_k/100), MARB = Maximum Acceptable Relative Bias.
This down-weights projects with inherently high uncertainty (e.g., low activity).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_year, get_our_labcode, load_all_years
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


def plot_year_rdi(df, year, save=True):
    """Scatter plot: each lab's RDI, sorted by RDI value."""
    lc_our = get_our_labcode(year)
    dy = df[df['year'] == year].dropna(subset=['rel_bias']).copy()
    # Weighted absolute bias: w_k = 1.2 / (1 + MARB/100), default weight=1.0
    dy['rdi_weight'] = dy['rdi_weight'].fillna(1.0)
    dy['weighted_abs_bias'] = dy['rel_bias'].abs() * dy['rdi_weight']

    # RDI stats use full data (ranks must be accurate)
    rdi_stats = dy.groupby('labcode').agg(
        n_projects=('rel_bias', 'count'),
        rdi=('weighted_abs_bias', 'mean'),
        rdi_raw=('rel_bias', lambda x: x.abs().mean()),
        median_abs_bias=('rel_bias', lambda x: x.abs().median()),
    ).reset_index()
    rdi_stats = rdi_stats.sort_values('rdi', ascending=True).reset_index(drop=True)
    rdi_stats['rank'] = range(1, len(rdi_stats) + 1)
    n_labs = len(rdi_stats)

    fig, ax = plt.subplots(figsize=(max(12, n_labs * 0.06), 6))

    x = np.arange(n_labs)

    # Other labs (circle)
    other_mask = rdi_stats['labcode'] != lc_our
    ax.scatter(x[other_mask], rdi_stats.loc[other_mask, 'rdi'],
               s=rdi_stats.loc[other_mask, 'n_projects'] * 2,
               color=YEAR_COLORS.get(year, '#999'), alpha=0.5,
               label='Other labs (size = n projects)', zorder=3)

    # Benchmark reference lines — computed from labs with RDI <= 100% for readability
    rdi_visible = rdi_stats[rdi_stats['rdi'] <= 100]
    all_mean = rdi_visible['rdi'].mean() if len(rdi_visible) > 0 else 0
    all_median = rdi_visible['rdi'].median() if len(rdi_visible) > 0 else 0
    ax.axhline(y=all_mean, color='#607D8B', ls='--', lw=1, alpha=0.7,
               label=f'All labs mean RDI = {all_mean:.1f}%')
    ax.axhline(y=all_median, color='#607D8B', ls=':', lw=1, alpha=0.5,
               label=f'All labs median RDI = {all_median:.1f}%')

    # Our lab - highlighted
    our_mask = rdi_stats['labcode'] == lc_our
    if our_mask.any():
        our_idx = np.where(our_mask)[0][0]
        our_row = rdi_stats[our_mask].iloc[0]
        ax.scatter(our_idx, our_row['rdi'], s=100, color='#E91E63', marker='D',
                   edgecolors='black', linewidth=1.0, zorder=5,
                   label=f'Our lab ({lc_our})')
        ax.annotate(f'#{int(our_row["rank"])}/{n_labs}\nRDI={our_row["rdi"]:.1f}% (n={int(our_row["n_projects"])})',
                    (our_idx, our_row['rdi']),
                    textcoords="offset points", xytext=(0, 16), ha='center',
                    fontsize=9, fontweight='bold', color='#E91E63')

    ax.set_ylabel('Result Deviation Index (RDI) [%]', fontsize=11)
    ax.set_xlabel('Laboratory (sorted by RDI, lower = better)', fontsize=10)
    ax.legend(fontsize=6, loc='upper left', markerscale=0.7, handletextpad=0.3,
              borderpad=0.3, labelspacing=0.2)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 100)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, f'rdi_scatter_{year}.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, f'rdi_scatter_{year}.pdf'))
    plt.close(fig)
    return rdi_stats


def plot_rdi_trend(yearly_data, our_rdi_df, save=True):
    """Our lab's RDI trend vs all labs benchmark."""
    fig, ax = plt.subplots(figsize=(9, 6))
    years = sorted(yearly_data.keys())

    bench_means = []
    bench_stds = []
    for y in years:
        rdi_vals = yearly_data[y]['rdi'].values
        rdi_vals = rdi_vals[rdi_vals <= 100]  # exclude extremes for display
        bench_means.append(np.mean(rdi_vals) if len(rdi_vals) > 0 else 0)
        bench_stds.append(np.std(rdi_vals) if len(rdi_vals) > 0 else 0)

    ax.fill_between(years,
                    np.array(bench_means) - np.array(bench_stds),
                    np.array(bench_means) + np.array(bench_stds),
                    alpha=0.15, color='#607D8B', label='All labs mean ± 1σ')
    ax.plot(years, bench_means, 's--', color='#607D8B', lw=1.5, markersize=6, label='All labs mean RDI')

    ax.errorbar(our_rdi_df['year'], our_rdi_df['rdi'], yerr=our_rdi_df['sem'],
                fmt='o-', color='#E91E63', lw=2.5, markersize=10, capsize=5, capthick=2,
                label='Our lab RDI', zorder=5)

    ax.set_xticks(years)
    ax.set_xlabel('Year')
    ax.set_ylabel('Result Deviation Index (RDI) [%]')
    ax.set_ylim(0, 50)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    for _, row in our_rdi_df.iterrows():
        ax.annotate(f'{row["rdi"]:.1f}±{row["sem"]:.1f}%\n(n={int(row["n_projects"])})',
                    (row['year'], row['rdi']),
                    textcoords="offset points", xytext=(0, 18), ha='center', fontsize=8)

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_trend.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_trend.pdf'))
    plt.close(fig)


def plot_rdi_ranking(df, save=True):
    """Our lab's weighted RDI rank among all labs."""
    fig, ax = plt.subplots(figsize=(8, 5))
    years = [2021, 2022, 2023, 2024, 2025]
    our_ranks = []

    for year in years:
        lc = get_our_labcode(year)
        dy = df[df['year'] == year].dropna(subset=['rel_bias']).copy()
        # Weighted RDI
        dy['rdi_weight'] = dy['rdi_weight'].fillna(1.0)
        dy['weighted_abs_bias'] = dy['rel_bias'].abs() * dy['rdi_weight']
        rdi_by_lab = dy.groupby('labcode')['weighted_abs_bias'].mean().sort_values()
        our_rdi = dy[dy['labcode'] == lc]['weighted_abs_bias'].mean()
        rank = (rdi_by_lab < our_rdi).sum() + 1
        our_ranks.append({'year': year, 'rank': rank, 'n_labs': len(rdi_by_lab)})

    or_df = pd.DataFrame(our_ranks)
    ax.plot(or_df['year'], or_df['rank'], 'o-', color='#FF5722', lw=2.5, markersize=10, zorder=4)
    ax.set_xticks(years)
    ax.set_ylabel('RDI Rank (lower = better)')
    ax.invert_yaxis()
    ax.grid(alpha=0.3)
    for _, row in or_df.iterrows():
        ax.annotate(f'#{row["rank"]}/{row["n_labs"]}', (row['year'], row['rank']),
                    textcoords="offset points", xytext=(0, -16), ha='center',
                    fontsize=9, fontweight='bold')

    fig.tight_layout()
    if save:
        fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_ranking.png'))
        fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_ranking.pdf'))
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_df = load_all_years()
    yearly_data = {}

    # Our lab's RDI summary
    rdi_summary = []

    for year in [2021, 2022, 2023, 2024, 2025]:
        print(f'Processing {year}...')
        df = load_year(year)
        rdi_stats = plot_year_rdi(df, year)
        yearly_data[year] = rdi_stats

        lc = get_our_labcode(year)
        our = rdi_stats[rdi_stats['labcode'] == lc]
        if len(our) > 0:
            r = our.iloc[0]
            our_dy = df[(df['year'] == year) & (df['labcode'] == lc)].dropna(subset=['rel_bias']).copy()
            our_dy['rdi_weight'] = our_dy['rdi_weight'].fillna(1.0)
            weighted_abs = our_dy['rel_bias'].abs() * our_dy['rdi_weight']
            w_rdi = weighted_abs.mean()
            sem = weighted_abs.std() / np.sqrt(len(weighted_abs)) if len(weighted_abs) > 1 else 0
            rdi_summary.append({
                'year': year, 'our_labcode': lc, 'n_projects': len(weighted_abs),
                'rdi': w_rdi, 'rdi_raw': our_dy['rel_bias'].abs().mean(),
                'sem': sem,
                'median_abs_bias': our_dy['rel_bias'].abs().median(),
                'rank': int(r['rank']), 'n_labs': len(rdi_stats),
            })
            print(f'  {year}: #{int(r["rank"])}/{len(rdi_stats)} rank, RDI={w_rdi:.2f}% (raw={our_dy["rel_bias"].abs().mean():.2f}%)')

    rdi_df = pd.DataFrame(rdi_summary)
    rdi_df.to_csv(os.path.join(OUTPUT_DIR, 'rdi_summary.csv'), index=False)

    # Trend & ranking
    plot_rdi_trend(yearly_data, rdi_df)
    plot_rdi_ranking(all_df)

    # Boxplot (keep existing functionality)
    fig, ax = plt.subplots(figsize=(8, 5))
    years = [2021, 2022, 2023, 2024, 2025]
    data_per_year = {}
    for year in years:
        lc = get_our_labcode(year)
        dy = all_df[all_df['year'] == year]
        our = dy[dy['labcode'] == lc].dropna(subset=['rel_bias'])
        data_per_year[year] = our['rel_bias'].abs().values

    bp = ax.boxplot([data_per_year[y] for y in years], tick_labels=[str(y) for y in years],
                    patch_artist=True, widths=0.5)
    for patch, y in zip(bp['boxes'], years):
        patch.set_facecolor(plt.cm.tab10(years.index(y)))
        patch.set_alpha(0.6)

    for i, y in enumerate(years):
        d = data_per_year[y]
        jitter = np.random.normal(0, 0.06, len(d))
        ax.scatter(np.full(len(d), i + 1) + jitter, d, alpha=0.5, s=25,
                   color=plt.cm.tab10(i), edgecolors='white', linewidth=0.3, zorder=4)

    ax.set_ylabel('Absolute Relative Bias [%]')
    ax.set_xlabel('Year')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=rdi_df['rdi'].mean(), color='red', ls='--', lw=1, alpha=0.5,
               label=f'5-year mean RDI={rdi_df["rdi"].mean():.1f}%')
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_boxplot.png'))
    fig.savefig(os.path.join(OUTPUT_DIR, 'rdi_boxplot.pdf'))
    plt.close(fig)

    print(f'\nRDI Summary:')
    print(rdi_df.to_string())
    print(f'\n5-year mean RDI: {rdi_df["rdi"].mean():.2f}%')


if __name__ == '__main__':
    main()
