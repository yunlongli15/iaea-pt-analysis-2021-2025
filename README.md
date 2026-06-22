# IAEA PT Multi-dimensional Analysis (2021–2025)

Long-term performance assessment of a radiological laboratory in IAEA Proficiency Tests, applying a six-dimensional statistical framework to 135 measurements across five consecutive PT rounds.

## Project Structure

```
├── 01_difficulty_pass_rate/        # Analysis 1: Difficulty coefficients & pass rates
│   ├── plot_difficulty_pass_rate.py
│   ├── difficulty_summary.csv
│   └── *.pdf / *.png               # Generated figures
│
├── 02_difficulty_trend/            # Analysis 2: Temporal difficulty trends
│   ├── plot_difficulty_trend.py
│   ├── difficulty_trends.csv
│   └── *.pdf / *.png
│
├── 03_lab_performance/             # Analysis 3: Inter-laboratory ranking
│   ├── plot_lab_performance.py
│   ├── lab_rankings_detail.csv
│   ├── lab_summary.csv
│   └── *.pdf / *.png
│
├── 04_difficulty_tier/             # Analysis 4: Difficulty-tier stratification
│   ├── plot_difficulty_tier.py
│   ├── difficulty_tier_summary.csv
│   └── *.pdf / *.png
│
├── 05_deviation_index/             # Analysis 5: Weighted Result Deviation Index (RDI)
│   ├── plot_deviation_index.py
│   ├── rdi_summary.csv
│   └── *.pdf / *.png
│
├── 06_relative_bias/               # Analysis 6: Within-project relative bias ranking
│   ├── plot_relative_bias.py
│   ├── plot_decay_chain_nw_breakdown.py
│   ├── ranking_*.csv
│   └── *.pdf / *.png
│
├── utils/                          # Shared utilities
│   ├── data_loader.py              # Excel file parser, MARB loader, lab code mapping
│   └── statistical_tests.py        # Mann-Kendall, Wilcoxon, Kruskal-Wallis, etc.
│
├── merged_labcode_tables_2021/     # Raw Excel data (one file per PT project)
├── merged_labcode_tables_2022/
├── merged_labcode_tables_2023/
├── merged_labcode_tables_2024/
├── merged_labcode_tables_2025/
│
├── .gitignore
├── CLAUDE.md                       # Project-specific AI assistant guidelines
└── README.md                       # This file
```

## Six Analytical Dimensions

1. **Difficulty Coefficients** — `D = 1 − N_A / N_all_labs`, with four tiers (Very Easy / Easy / Moderate / Hard)
2. **Temporal Difficulty Trends** — Cross-year matching of nuclide–matrix pairs, Mann–Kendall trend tests
3. **Inter-laboratory Ranking** — Participation breadth, A-score counts, and within-project percentile ranks
4. **Difficulty-tier Stratification** — Pass rates by tier vs. global averages with Wilson CIs
5. **Weighted RDI** — `RDI = (1/K) Σ w_k · |RB_k|`, where `w_k = 1.2 / (1 + MARB_k/100%)`
6. **Relative Bias Ranking** — Within-project |RB| ranking, bias heatmaps, technique-specific diagnostics

## Key Results

- Overall pass rate: **98.5%** (133/135 Acceptable), zero "Not Acceptable"
- Weighted RDI 5-year mean: **3.05%** (consistently below global benchmark)
- Hard-tier pass rate: **91.7%** vs. global **63.2%**
- Wilcoxon signed-rank: our |RB| significantly lower than peer median (**p < 0.001**, 97/109 projects)

## Reproducing the Analysis

```bash
# Requirements: Python 3.11+, pandas, numpy, scipy, matplotlib, openpyxl

# Regenerate all figures
python 01_difficulty_pass_rate/plot_difficulty_pass_rate.py
python 02_difficulty_trend/plot_difficulty_trend.py
python 03_lab_performance/plot_lab_performance.py
python 04_difficulty_tier/plot_difficulty_tier.py
python 05_deviation_index/plot_deviation_index.py
python 06_relative_bias/plot_relative_bias.py

# Run statistical inference
python utils/statistical_tests.py
```

## Data Source

IAEA Terrestrial Environmental Radiochemistry Centre (TERC) proficiency test summary reports (2021–2025), available at:  
https://analytical-reference-materials.iaea.org/previous-proficiency-tests
