"""
Analysis 4: Our lab's performance across different difficulty tiers.
Group projects by difficulty and show participation/pass counts.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_all_years, get_our_labcode
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

TIER_LABELS = ['Very Easy\n(<0.6)', 'Easy\n(0.6–0.8)',
               'Moderate\n(0.8–0.9)', 'Hard\n(≥0.9)']
TIER_ORDER = ['Very Easy', 'Easy', 'Moderate', 'Hard']
TIER_COLORS = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']

plt.rcParams.update({
    'font.size': 9, 'axes.titlesize': 11, 'axes.labelsize': 10,
    'figure.dpi': 150, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
})


def classify_tier(difficulty):
    if difficulty < 0.6:
        return 'Very Easy'
    elif difficulty <= 0.8:
        return 'Easy'
    elif difficulty <= 0.9:
        return 'Moderate'
    else:
        return 'Hard'


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_all_years()

    # Compute difficulty for ALL projects (all years)
    n_all_labs_per_year = df.groupby('year')['labcode'].nunique()

    all_stats = df.groupby(['project', 'year']).agg(
        n_total=('labcode', 'count'),
        n_pass=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    all_stats['n_all_labs'] = all_stats['year'].map(n_all_labs_per_year)
    all_stats['difficulty'] = 1 - all_stats['n_pass'] / all_stats['n_all_labs']
    all_stats['tier'] = all_stats['difficulty'].apply(classify_tier)

    # Our lab data
    our_data = []
    for year in [2021, 2022, 2023, 2024, 2025]:
        lc = get_our_labcode(year)
        dy = df[df['year'] == year]
        our = dy[dy['labcode'] == lc]
        for _, row in our.iterrows():
            proj = row['project']
            s = all_stats[(all_stats['project'] == proj) & (all_stats['year'] == year)]
            diff = s['difficulty'].values[0] if len(s) > 0 else np.nan
            our_data.append({
                'year': year,
                'project': proj,
                'difficulty': diff,
                'tier': classify_tier(diff) if not np.isnan(diff) else 'Unknown',
                'final_score': row['final_score'],
                'passed': 1 if row['final_score'] == 'A' else 0,
            })
    our_df = pd.DataFrame(our_data)

    # ============================================================
    # Figure 1: Counts by tier per year — 2-row layout, bottom centered
    # ============================================================
    years = [2021, 2022, 2023, 2024, 2025]
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 6, figure=fig, hspace=0.35, wspace=0.3)
    # Row 1: 3 subplots spanning 2 cols each
    ax_positions = [
        fig.add_subplot(gs[0, 0:2]),
        fig.add_subplot(gs[0, 2:4]),
        fig.add_subplot(gs[0, 4:6]),
        fig.add_subplot(gs[1, 1:3]),   # centered in bottom row
        fig.add_subplot(gs[1, 3:5]),
    ]

    for idx, year in enumerate(years):
        ax = ax_positions[idx]
        year_data = our_df[our_df['year'] == year]
        year_all = all_stats[all_stats['year'] == year]

        participated = []
        passed_list = []
        total_list = []
        for tier in TIER_ORDER:
            td = year_data[year_data['tier'] == tier]
            participated.append(len(td))
            passed_list.append(td['passed'].sum())
            # Total distinct projects in this tier this year
            ta = year_all[year_all['tier'] == tier]
            total_list.append(ta['project'].nunique())

        x = np.arange(len(TIER_ORDER))
        w = 0.25
        ax.bar(x - w, participated, w, color='#90CAF9', label='We participated', zorder=3)
        ax.bar(x, passed_list, w, color='#1976D2', label='We passed', zorder=3)
        ax.bar(x + w, total_list, w, color='#E0E0E0', edgecolor='#999', linewidth=0.8,
               label='Total offered', zorder=2)

        for i, (p, s, t) in enumerate(zip(participated, passed_list, total_list)):
            if p > 0:
                ax.text(i - w, p + 0.2, str(p), ha='center', fontsize=8, fontweight='bold', color='#1565C0')
            if s > 0:
                ax.text(i, s + 0.2, str(s), ha='center', fontsize=8, fontweight='bold', color='#0D47A1')
            if t > 0:
                ax.text(i + w, t + 0.2, str(t), ha='center', fontsize=7, color='#757575')

        ax.set_xticks(x)
        ax.set_xticklabels(TIER_LABELS, fontsize=8)
        ax.set_ylabel('Count')
        all_vals = participated + passed_list + total_list
        ymax = max(all_vals) if all_vals else 1
        ax.set_ylim(0, ymax * 1.25 + 0.5)
        ax.legend(fontsize=6.5, loc='upper right', ncol=3)
        ax.grid(axis='y', alpha=0.3)

    fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_tier_counts.png'))
    fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_tier_counts.pdf'))
    plt.close(fig)

    # ============================================================
    # Figure 2: Pass rate by tier — our lab vs global (all years)
    # ============================================================
    fig, ax = plt.subplots(figsize=(10, 5.5))

    # Global pass rate per tier (all labs, all years)
    global_rates = []
    global_n = []
    for tier in TIER_ORDER:
        td = all_stats[all_stats['tier'] == tier]
        total_pass = td['n_pass'].sum()
        total_labs = td['n_total'].sum()
        global_rates.append(total_pass / total_labs * 100 if total_labs > 0 else 0)
        global_n.append(total_labs)

    # Our pass rate per tier
    our_rates = []
    our_n = []
    for tier in TIER_ORDER:
        td = our_df[our_df['tier'] == tier]
        total = len(td)
        passed = td['passed'].sum()
        our_rates.append(passed / total * 100 if total > 0 else 0)
        our_n.append(total)

    x = np.arange(len(TIER_ORDER))
    w = 0.32
    bars1 = ax.bar(x - w/2, our_rates, w, color='#1976D2', alpha=0.9, zorder=3,
                   label='Our lab')
    bars2 = ax.bar(x + w/2, global_rates, w, color='#BDBDBD', alpha=0.85, zorder=3,
                   label='Global (all labs)')

    # Annotate
    for i, (our, gl, on_, gn) in enumerate(zip(our_rates, global_rates, our_n, global_n)):
        ax.text(i - w/2, our + 1.5, f'{our:.1f}%\n(n={on_})', ha='center',
                fontsize=8, fontweight='bold', color='#1976D2')
        ax.text(i + w/2, gl + 1.5, f'{gl:.1f}%\n(n={gn})', ha='center',
                fontsize=7, color='#757575')

    ax.set_xticks(x)
    ax.set_xticklabels(TIER_LABELS, fontsize=9)
    ax.set_ylabel('Pass Rate (%)')
    ax.set_ylim(0, 115)
    ax.legend(fontsize=9, loc='lower left')
    ax.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_tier_pass_rate.png'))
    fig.savefig(os.path.join(OUTPUT_DIR, 'difficulty_tier_pass_rate.pdf'))
    plt.close(fig)

    # Summary table
    summary_rows = []
    for tier in TIER_ORDER:
        td = our_df[our_df['tier'] == tier]
        for year in years:
            ytd = td[td['year'] == year]
            if len(ytd) > 0:
                summary_rows.append({
                    'Tier': tier, 'Year': year,
                    'Participated': len(ytd), 'Passed': ytd['passed'].sum(),
                    'Pass Rate': f'{ytd["passed"].mean()*100:.1f}%'
                })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(os.path.join(OUTPUT_DIR, 'difficulty_tier_summary.csv'), index=False)
    print(summary.to_string())


if __name__ == '__main__':
    main()
