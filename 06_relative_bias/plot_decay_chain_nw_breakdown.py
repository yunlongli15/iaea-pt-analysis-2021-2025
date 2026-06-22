"""
Plot N (trueness fail) vs W (precision fail) breakdown + bias direction
for 2025 soil U-Ra decay chain projects. Two separate figures, no titles.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils'))
from data_loader import load_year
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

TARGETS = ['U-238 Gamma Soil', 'Th-234 Gamma Soil', 'Pa-234m Gamma Soil',
           'Ra-226 Gamma Soil', 'Pb-214 Gamma Soil', 'Bi-214 Gamma Soil']


def main():
    df = load_year(2025)

    labels = []
    n_vals, w_vals = [], []
    rb_means, rb_medians = [], []

    for tgt in TARGETS:
        projs = [p for p in df['project'].unique() if tgt in p]
        if not projs:
            continue
        group = df[df['project'] == projs[0]].dropna(subset=['rel_bias'])
        n_vals.append((group['final_score'] == 'N').sum())
        w_vals.append((group['final_score'] == 'W').sum())
        rb_means.append(group['rel_bias'].mean())
        rb_medians.append(group['rel_bias'].median())
        label = projs[0].split(' - ')[1] if ' - ' in projs[0] else projs[0]
        labels.append(label)

    # ===== Figure 1: N vs W grouped bar =====
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    x = np.arange(len(labels))
    width = 0.35

    bars_n = ax1.bar(x - width / 2, n_vals, width, color='#E53935', alpha=0.85,
                     edgecolor='white', label='Not Accepted (Trueness fail)')
    bars_w = ax1.bar(x + width / 2, w_vals, width, color='#FFA726', alpha=0.85,
                     edgecolor='white', label='Warning (Precision fail)')

    for bar, n in zip(bars_n, n_vals):
        if n > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(n), ha='center', va='bottom', fontsize=8, fontweight='bold', color='#C62828')
    for bar, w in zip(bars_w, w_vals):
        if w > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     str(w), ha='center', va='bottom', fontsize=8, fontweight='bold', color='#E65100')

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax1.set_ylabel('Number of Laboratories', fontsize=11)
    ax1.legend(fontsize=8, loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, max(max(n_vals), max(w_vals)) * 1.15)

    fig1.tight_layout()
    fig1.savefig(os.path.join(OUTPUT_DIR, 'decay_chain_nw_breakdown.pdf'))
    fig1.savefig(os.path.join(OUTPUT_DIR, 'decay_chain_nw_breakdown.png'))
    plt.close(fig1)

    # ===== Figure 2: RB direction bar =====
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    colors = ['#E53935' if m > 0 else '#1565C0' for m in rb_means]
    ax2.bar(x, rb_means, width * 1.2, color=colors, alpha=0.8, edgecolor='white')
    ax2.scatter(x, rb_medians, color='black', s=40, zorder=5, marker='D', label='Median RB')

    for i, (m, md) in enumerate(zip(rb_means, rb_medians)):
        ax2.text(i, m + (3 if m > 0 else -8),
                 f'mean={m:+.1f}%', ha='center', va='bottom' if m > 0 else 'top',
                 fontsize=7.5, fontweight='bold')
        ax2.text(i, md + (2 if md > 0 else -5),
                 f'med={md:+.1f}%', ha='center', va='bottom' if md > 0 else 'top',
                 fontsize=6.5, color='#333')

    ax2.axhline(y=0, color='black', lw=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax2.set_ylabel('Relative Bias (%)', fontsize=11)
    ax2.legend(fontsize=8)
    ax2.grid(axis='y', alpha=0.3)

    fig2.tight_layout()
    fig2.savefig(os.path.join(OUTPUT_DIR, 'decay_chain_bias_direction.pdf'))
    fig2.savefig(os.path.join(OUTPUT_DIR, 'decay_chain_bias_direction.png'))
    plt.close(fig2)

    print('Saved:')
    print(f'  {OUTPUT_DIR}/decay_chain_nw_breakdown.pdf')
    print(f'  {OUTPUT_DIR}/decay_chain_bias_direction.pdf')


if __name__ == '__main__':
    main()
