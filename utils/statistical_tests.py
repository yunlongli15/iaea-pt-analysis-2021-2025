"""
Statistical inference module for IAEA PT analysis.
Computes trend tests, confidence intervals, and hypothesis tests
to support inferential claims in the paper.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import load_all_years, get_our_labcode
import numpy as np
import pandas as pd
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


def mann_kendall(x):
    """Mann-Kendall trend test. Returns (statistic, p_value, trend_direction).
    Positive S = upward trend; negative S = downward trend."""
    n = len(x)
    if n < 3:
        return 0, 1.0, 'insufficient data'
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += np.sign(x[j] - x[i])
    # Variance
    var_s = (n * (n - 1) * (2 * n + 5)) / 18
    # Handle ties
    unique_vals, counts = np.unique(x, return_counts=True)
    for t in counts:
        if t > 1:
            var_s -= (t * (t - 1) * (2 * t + 5)) / 18
    if var_s <= 0:
        var_s = 1e-10
    z = (s - np.sign(s)) / np.sqrt(var_s)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    trend = 'increasing' if s > 0 else 'decreasing' if s < 0 else 'no trend'
    return s, p, trend


def compute_all_statistics():
    """Compute all statistical tests and return formatted results."""
    df = load_all_years()
    years = [2021, 2022, 2023, 2024, 2025]
    results = {}

    # ============================================================
    # 1. Difficulty trend (Mann-Kendall on annual mean difficulty)
    # ============================================================
    n_all_labs_per_year = df.groupby('year')['labcode'].nunique()
    all_stats = df.groupby(['project', 'year']).agg(
        n_pass=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    all_stats['n_all_labs'] = all_stats['year'].map(n_all_labs_per_year)
    all_stats['difficulty'] = 1 - all_stats['n_pass'] / all_stats['n_all_labs']

    annual_mean_d = all_stats.groupby('year')['difficulty'].mean()
    s_d, p_d, trend_d = mann_kendall(annual_mean_d.values)
    results['difficulty_trend'] = {
        'annual_means': annual_mean_d.to_dict(),
        'mk_S': s_d,
        'mk_p': p_d,
        'mk_trend': trend_d,
        'n_years': len(years),
    }

    # ============================================================
    # 2. Mean pass rate trend (Mann-Kendall)
    # ============================================================
    all_stats['pass_rate'] = all_stats['n_pass'] / df.groupby(['project', 'year'])['labcode'].count().reindex(
        pd.MultiIndex.from_frame(all_stats[['project', 'year']])).values
    annual_mean_pr = all_stats.groupby('year')['pass_rate'].mean()
    s_pr, p_pr, trend_pr = mann_kendall(annual_mean_pr.values)
    results['pass_rate_trend'] = {
        'annual_means': annual_mean_pr.to_dict(),
        'mk_S': s_pr,
        'mk_p': p_pr,
        'mk_trend': trend_pr,
    }

    # ============================================================
    # 3. Our lab's RDI trend (Mann-Kendall)
    # ============================================================
    rdi_values = []
    rdi_sems = []
    for year in years:
        lc = get_our_labcode(year)
        dy = df[(df['year'] == year) & (df['labcode'] == lc)].dropna(subset=['rel_bias']).copy()
        dy['rdi_weight'] = dy['rdi_weight'].fillna(1.0)
        weighted_abs = dy['rel_bias'].abs() * dy['rdi_weight']
        rdi_values.append(weighted_abs.mean())
        rdi_sems.append(weighted_abs.std() / np.sqrt(len(weighted_abs)) if len(weighted_abs) > 1 else 0)

    s_rdi, p_rdi, trend_rdi = mann_kendall(np.array(rdi_values))
    results['rdi_trend'] = {
        'annual_rdi': dict(zip(years, rdi_values)),
        'annual_sem': dict(zip(years, rdi_sems)),
        'five_year_mean_weighted': np.mean(rdi_values),
        'mk_S': s_rdi,
        'mk_p': p_rdi,
        'mk_trend': trend_rdi,
    }

    # ============================================================
    # 4. Our percentile rank trend and Kruskal-Wallis test
    # ============================================================
    percentile_data = {}
    all_percentiles = []
    for year in years:
        lc = get_our_labcode(year)
        dy = df[df['year'] == year].dropna(subset=['rel_bias'])
        percs = []
        for proj, group in dy.groupby('project'):
            group = group.copy()
            group['abs_bias'] = group['rel_bias'].abs()
            n_total = len(group)
            if lc not in group['labcode'].values:
                continue
            our_abs = group[group['labcode'] == lc]['abs_bias'].values[0]
            rank = (group['abs_bias'] < our_abs).sum() + 1
            percs.append(rank / n_total * 100)
        percentile_data[year] = percs
        all_percentiles.extend([(year, p) for p in percs])

    # Mann-Kendall on annual mean percentiles
    annual_mean_perc = {y: np.mean(v) for y, v in percentile_data.items()}
    s_perc, p_perc, trend_perc = mann_kendall(np.array(list(annual_mean_perc.values())))

    # Kruskal-Wallis: test if percentile distributions differ across years
    perc_groups = [np.array(v) for v in percentile_data.values()]
    h_stat, p_kw = stats.kruskal(*perc_groups)

    # 95% CI for overall mean percentile (bootstrapped)
    all_vals = np.concatenate(perc_groups)
    n_boot = 10000
    boot_means = np.array([np.mean(np.random.choice(all_vals, size=len(all_vals), replace=True))
                           for _ in range(n_boot)])
    ci_low = np.percentile(boot_means, 2.5)
    ci_high = np.percentile(boot_means, 97.5)

    results['percentile_analysis'] = {
        'annual_means': annual_mean_perc,
        'annual_medians': {y: np.median(v) for y, v in percentile_data.items()},
        'overall_mean': np.mean(all_vals),
        'ci_95': (ci_low, ci_high),
        'mk_S': s_perc,
        'mk_p': p_perc,
        'mk_trend': trend_perc,
        'kruskal_wallis_H': h_stat,
        'kruskal_wallis_p': p_kw,
    }

    # ============================================================
    # 5. Wilcoxon signed-rank: our |RB| vs all-lab median per project
    # ============================================================
    our_diffs = []
    for year in years:
        lc = get_our_labcode(year)
        dy = df[df['year'] == year].dropna(subset=['rel_bias'])
        for proj, group in dy.groupby('project'):
            group = group.copy()
            group['abs_bias'] = group['rel_bias'].abs()
            if lc not in group['labcode'].values:
                continue
            our_abs = group[group['labcode'] == lc]['abs_bias'].values[0]
            all_median = group['abs_bias'].median()
            our_diffs.append(our_abs - all_median)

    if len(our_diffs) > 0:
        w_stat, w_p = stats.wilcoxon(our_diffs, alternative='less')
        n_neg = sum(1 for d in our_diffs if d < 0)  # cases where our |bias| < median
        n_pos = sum(1 for d in our_diffs if d > 0)
    else:
        w_stat, w_p, n_neg, n_pos = np.nan, np.nan, 0, 0

    results['wilcoxon'] = {
        'n_total': len(our_diffs),
        'n_below_median': n_neg,
        'n_above_median': n_pos,
        'mean_diff': np.mean(our_diffs),
        'statistic': w_stat,
        'p_value': w_p,
    }

    # ============================================================
    # 6. Difficulty tier pass rates with 95% CIs (Wilson score interval)
    # ============================================================
    def wilson_ci(n_pass, n_total, alpha=0.05):
        """Wilson score interval for a proportion."""
        if n_total == 0:
            return 0, 0, 0
        p_hat = n_pass / n_total
        z = stats.norm.ppf(1 - alpha / 2)
        denom = 1 + z**2 / n_total
        center = (p_hat + z**2 / (2 * n_total)) / denom
        margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_total)) / n_total) / denom
        return p_hat, max(0, center - margin), min(1, center + margin)

    tier_results = {}
    n_all_labs_per_year_2 = df.groupby('year')['labcode'].nunique()
    tier_projects = df.groupby(['project', 'year']).agg(
        n_total=('labcode', 'count'),
        n_pass=('final_score', lambda x: (x == 'A').sum()),
    ).reset_index()
    tier_projects['n_all_labs'] = tier_projects['year'].map(n_all_labs_per_year_2)
    tier_projects['difficulty'] = 1 - tier_projects['n_pass'] / tier_projects['n_all_labs']
    tier_projects['tier'] = pd.cut(tier_projects['difficulty'],
                                    bins=[-0.01, 0.6, 0.8, 0.9, 1.01],
                                    labels=['Very Easy', 'Easy', 'Moderate', 'Hard'])

    for tier in ['Very Easy', 'Easy', 'Moderate', 'Hard']:
        td = tier_projects[tier_projects['tier'] == tier]
        n_pass = td['n_pass'].sum()
        n_total = td['n_total'].sum()
        p, ci_l, ci_h = wilson_ci(n_pass, n_total)
        tier_results[tier] = {'pass_rate': p*100, 'ci_low': ci_l*100, 'ci_high': ci_h*100,
                              'n_pass': n_pass, 'n_total': n_total}
    results['tier_cis'] = tier_results

    # ============================================================
    # 7. Correlation: RDI vs participation breadth
    # ============================================================
    rdi_vs_n = []
    for year in years:
        dy = df[df['year'] == year].dropna(subset=['rel_bias']).copy()
        dy['rdi_weight'] = dy['rdi_weight'].fillna(1.0)
        dy['weighted_abs_bias'] = dy['rel_bias'].abs() * dy['rdi_weight']
        rdi_by_lab = dy.groupby('labcode')['weighted_abs_bias'].mean()
        n_by_lab = dy.groupby('labcode')['rel_bias'].count()
        common = rdi_by_lab.index.intersection(n_by_lab.index)
        if len(common) > 1:
            r, p_spear = stats.spearmanr(rdi_by_lab[common], n_by_lab[common])
            rdi_vs_n.append({'year': year, 'spearman_r': r, 'spearman_p': p_spear, 'n_labs': len(common)})

    results['rdi_vs_n'] = rdi_vs_n

    return results


def print_report(results):
    """Print a formatted statistical report."""
    print("=" * 70)
    print("STATISTICAL INFERENCE REPORT")
    print("IAEA PT Multi-dimensional Analysis (2021-2025)")
    print("=" * 70)

    # 1. Difficulty trend
    d = results['difficulty_trend']
    print(f"\n1. PROJECT DIFFICULTY TREND (Mann-Kendall)")
    print(f"   Annual means: {', '.join(f'{y}: {v:.3f}' for y, v in d['annual_means'].items())}")
    print(f"   S = {d['mk_S']}, p = {d['mk_p']:.4f}")
    print(f"   Trend: {d['mk_trend']}")
    if d['mk_p'] < 0.05:
        print(f"   → Statistically significant at α = 0.05")
    else:
        print(f"   → Not statistically significant at α = 0.05")

    # 2. Pass rate trend
    pr = results['pass_rate_trend']
    print(f"\n2. MEAN PASS RATE TREND (Mann-Kendall)")
    print(f"   Annual means: {', '.join(f'{y}: {v:.3f}' for y, v in pr['annual_means'].items())}")
    print(f"   S = {pr['mk_S']}, p = {pr['mk_p']:.4f}")
    print(f"   Trend: {pr['mk_trend']}")
    if pr['mk_p'] < 0.05:
        print(f"   → Statistically significant at α = 0.05")
    else:
        print(f"   → Not statistically significant at α = 0.05")

    # 3. RDI trend
    rdi = results['rdi_trend']
    print(f"\n3. OUR LAB RDI TREND (Mann-Kendall)")
    for y, v in rdi['annual_rdi'].items():
        print(f"   {y}: {v:.2f}% ± {rdi['annual_sem'][y]:.2f}% (SEM)")
    print(f"   5-year weighted mean: {rdi['five_year_mean_weighted']:.2f}%")
    print(f"   S = {rdi['mk_S']}, p = {rdi['mk_p']:.4f}")
    if rdi['mk_p'] < 0.05:
        print(f"   → Statistically significant increasing trend (α = 0.05)")
    else:
        print(f"   → Not statistically significant at α = 0.05")

    # 4. Percentile analysis
    perc = results['percentile_analysis']
    print(f"\n4. PERCENTILE RANK ANALYSIS")
    for y in [2021, 2022, 2023, 2024, 2025]:
        print(f"   {y}: mean = {perc['annual_means'][y]:.1f}%, median = {perc['annual_medians'][y]:.1f}%")
    print(f"   Overall mean: {perc['overall_mean']:.1f}% (95% CI: {perc['ci_95'][0]:.1f}%–{perc['ci_95'][1]:.1f}%)")
    print(f"   Mann-Kendall: S = {perc['mk_S']}, p = {perc['mk_p']:.4f} ({perc['mk_trend']})")
    print(f"   Kruskal-Wallis: H = {perc['kruskal_wallis_H']:.2f}, p = {perc['kruskal_wallis_p']:.4f}")
    if perc['kruskal_wallis_p'] < 0.05:
        print(f"   → Significant year-to-year differences in percentile distributions")
    else:
        print(f"   → No significant year-to-year differences")

    # 5. Wilcoxon
    w = results['wilcoxon']
    print(f"\n5. WILCOXON SIGNED-RANK TEST (Our |RB| vs All-lab Median)")
    print(f"   N = {w['n_total']} project participations")
    print(f"   Our |bias| < median: {w['n_below_median']} / > median: {w['n_above_median']}")
    print(f"   Mean difference: {w['mean_diff']:.2f}%")
    print(f"   W = {w['statistic']:.0f}, p = {w['p_value']:.4f} (one-sided: our |bias| < median)")
    if w['p_value'] < 0.05:
        print(f"   → Our |RB| is significantly lower than the peer median")
    else:
        print(f"   → Not significantly lower than the peer median")

    # 6. Tier CIs
    print(f"\n6. DIFFICULTY TIER PASS RATES WITH 95% CIs (Wilson)")
    for tier, t in results['tier_cis'].items():
        print(f"   {tier}: {t['pass_rate']:.1f}% (95% CI: {t['ci_low']:.1f}%–{t['ci_high']:.1f}%) [n={t['n_total']}]")

    # 7. RDI vs N correlation
    print(f"\n7. SPEARMAN CORRELATION: RDI vs PARTICIPATION BREADTH")
    for rv in results['rdi_vs_n']:
        sig = "significant" if rv['spearman_p'] < 0.05 else "not significant"
        print(f"   {rv['year']}: ρ = {rv['spearman_r']:.3f}, p = {rv['spearman_p']:.4f} ({sig}), n = {rv['n_labs']} labs")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    results = compute_all_statistics()
    print_report(results)

    # Save results as JSON for paper integration
    import json
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'paper', 'statistical_results.json')
    # Convert numpy types for JSON
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        elif isinstance(obj, tuple):
            return [convert(v) for v in obj]
        return obj

    with open(output_path, 'w') as f:
        json.dump(convert(results), f, indent=2)
    print(f"\nResults saved to {output_path}")
