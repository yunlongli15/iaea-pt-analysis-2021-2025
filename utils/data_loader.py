"""
Common data loader for IAEA proficiency test results (2021-2025).
Handles variable column names, Z-Score-only files, and filename parsing.
"""
import pandas as pd
import numpy as np
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAB_CODES = {2021: 211, 2022: 8, 2023: 43, 2024: 5, 2025: 15}


def parse_project_name(filename, keep_prefix=True):
    """Extract a clean project label from the filename.
    If keep_prefix=True, preserves the leading numeric prefix for uniqueness."""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Extract leading number before stripping it
    prefix = ''
    num_match = re.match(r'^(\d+)_', name)
    if keep_prefix and num_match:
        prefix = num_match.group(1) + ' - '
    # Remove leading number (e.g., "01_", "001_")
    name = re.sub(r'^\d+_', '', name)
    # Remove "Labcode_Table_N_N-M_" prefix (2021/2022 format)
    name = re.sub(r'Labcode_Table_\d+_\d+-\d+_', '', name)
    # Remove "Labcode_N-M_" prefix (2023/2024 format)
    name = re.sub(r'Labcode_\d+-\d+_', '', name)
    # Remove "Labcode_N_" prefix (e.g., "Labcode_255_")
    name = re.sub(r'Labcode_\d+_', '', name)
    # Remove any leftover labcode range prefix (e.g., "255_", "1-325_")
    name = re.sub(r'^\d+-\d+_', '', name)
    name = re.sub(r'^\d+_', '', name)
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Clean up
    name = name.replace('ICPMS', 'ICP-MS')
    name = name.replace('SurFace', 'Surface')
    name = name.replace('PlantAsh', 'Plant Ash')
    return prefix + name


def _zscore_to_final(z):
    """Convert Z-Score to A/N/W based on conventional thresholds."""
    if pd.isna(z):
        return np.nan
    z_abs = abs(z)
    if z_abs <= 2:
        return 'A'
    elif z_abs < 3:
        return 'W'
    else:
        return 'N'


def load_single_file(filepath, year, keep_prefix=True):
    """Load a single Excel file and return a normalized DataFrame."""
    df = pd.read_excel(filepath)
    project_name = parse_project_name(filepath, keep_prefix=keep_prefix)
    project_core = parse_project_name(filepath, keep_prefix=False)

    # Normalize column names
    cols = {}
    for c in df.columns:
        if c.startswith('Unnamed'):
            continue
        c_stripped = c.strip()
        cols[c] = c_stripped

    # Find labcode column
    labcode_col = 'Labcode' if 'Labcode' in df.columns else None
    if labcode_col is None:
        return None

    # Find value / uncertainty / bias columns
    rep_val_col = None
    rep_unc_col = None
    rel_bias_col = None
    final_score_col = None

    for orig, clean in cols.items():
        if clean == 'Labcode':
            continue
        if clean.startswith('Rep. Value') or clean.startswith('Reported value') or clean.startswith('Reported  value'):
            rep_val_col = orig
        elif clean.startswith('Rep. Unc') or clean.startswith('Reported uncertainty'):
            rep_unc_col = orig
        elif clean.startswith('Rel. Bias') or clean.startswith('Relative bias'):
            rel_bias_col = orig
        elif clean in ('Final Score', 'Final', 'Z-Score Evaluation'):
            final_score_col = orig

    result = pd.DataFrame()
    result['labcode'] = df[labcode_col]
    result['project'] = project_name
    result['project_core'] = project_core
    result['year'] = year

    result['rep_value'] = df[rep_val_col] if rep_val_col else np.nan
    result['rep_unc'] = df[rep_unc_col] if rep_unc_col else np.nan
    result['rel_bias'] = df[rel_bias_col] if rel_bias_col else np.nan

    if final_score_col:
        result['final_score'] = df[final_score_col].astype(str).str.strip()
    elif 'Z-Score' in df.columns:
        result['final_score'] = df['Z-Score'].apply(_zscore_to_final)
    else:
        result['final_score'] = np.nan

    # Map Q (Questionable) to W for consistency
    result['final_score'] = result['final_score'].replace('Q', 'W')

    # Ensure numeric types
    for c in ['rep_value', 'rep_unc', 'rel_bias']:
        result[c] = pd.to_numeric(result[c], errors='coerce')

    # Remove rows without labcode
    result = result.dropna(subset=['labcode'])
    result['labcode'] = result['labcode'].astype(int)

    return result


def load_marbs(year):
    """Load MARB values for a year. Returns dict: project_name -> MARB (in %)."""
    folder = os.path.join(BASE_DIR, f'merged_labcode_tables_{year}')
    marb_path = os.path.join(folder, 'MARB.xlsx')
    if not os.path.exists(marb_path):
        return {}

    marb_df = pd.read_excel(marb_path, header=None)
    marb_values = marb_df.iloc[:, 0].values  # single column

    # Get sorted project files (same order as load_year) to match MARB rows
    files = sorted(glob.glob(os.path.join(folder, '*.xlsx')))
    files = [f for f in files if '~$' not in f and 'MARB' not in os.path.basename(f)]

    marb_map = {}
    for i, f in enumerate(files):
        if i < len(marb_values):
            proj_name = parse_project_name(f, keep_prefix=True)
            marb_map[proj_name] = float(marb_values[i])
    return marb_map


def load_year(year, keep_prefix=True):
    """Load all files for a given year, return combined DataFrame."""
    folder = os.path.join(BASE_DIR, f'merged_labcode_tables_{year}')
    if not os.path.exists(folder):
        raise FileNotFoundError(f'Folder not found: {folder}')

    # Load MARB values first
    marb_map = load_marbs(year)

    files = sorted(glob.glob(os.path.join(folder, '*.xlsx')))
    files = [f for f in files if '~$' not in f and 'MARB' not in os.path.basename(f)]

    dfs = []
    for f in files:
        df = load_single_file(f, year, keep_prefix=keep_prefix)
        if df is not None and len(df) > 0:
            dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    # Attach MARB and weight to each project
    result['marb'] = result['project'].map(marb_map)
    result['rdi_weight'] = 1.2 / (1 + result['marb'] / 100)

    # Deduplicate: keep first occurrence of each labcode-project-year combination
    n_before = len(result)
    result = result.drop_duplicates(subset=['labcode', 'project', 'year'], keep='first')
    n_removed = n_before - len(result)
    if n_removed > 0:
        print(f'  [dedup] Removed {n_removed} duplicate rows for {year}')
    return result


def load_all_years(years=None, keep_prefix=True):
    """Load all years, return combined DataFrame."""
    if years is None:
        years = [2021, 2022, 2023, 2024, 2025]
    dfs = [load_year(y, keep_prefix=keep_prefix) for y in years]
    return pd.concat(dfs, ignore_index=True)


def get_our_labcode(year):
    """Return our lab's code for the given year."""
    return LAB_CODES.get(year)
