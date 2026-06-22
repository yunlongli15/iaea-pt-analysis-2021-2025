import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

def analyze_single_year(year, special_lab=None):
    """
    Analyze laboratory bias deviation for a single year
    """
    # Set special labs for each year
    year_special_labs = {
        2021: ['211', 'lab211', 'labcode211'],
        2022: ['8', 'lab8', 'labcode8'],
        2023: ['43', 'lab43', 'labcode43'],
        2024: ['5', 'lab5', 'labcode5']
    }
    
    if special_lab is None and year in year_special_labs:
        special_labs = year_special_labs[year]
    else:
        special_labs = [special_lab] if special_lab else []
    
    # Construct folder path
    folder_path = f"merged_labcode_tables_{year}"
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Warning: Folder '{folder_path}' does not exist. Skipping year {year}.")
        return None, None, 0
    
    # Find all Excel files
    excel_files = glob.glob(f"{folder_path}/*.xlsx") + glob.glob(f"{folder_path}/*.xls")
    csv_files = glob.glob(f"{folder_path}/*.csv")
    all_files = excel_files + csv_files
    
    if not all_files:
        print(f"{year}: No data files found")
        return None, None, 0
    
    print(f"{year}: Found {len(all_files)} analysis project files")
    
    # Collect relative bias data for each lab
    lab_bias_data = defaultdict(list)  # Store all relative bias absolute values for each lab
    lab_file_count = defaultdict(int)  # Count files each lab participated in
    
    for file_path in all_files:
        try:
            # Read file
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                # Try different encodings
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except:
                        df = pd.read_csv(file_path, encoding='latin1')
            
            # Find labcode column and relative bias column
            labcode_col = None
            bias_col = None
            
            for col_name in df.columns:
                col_lower = str(col_name).lower()
                if 'labcode' in col_lower:
                    labcode_col = col_name
                elif 'relative bias' in col_lower:
                    bias_col = col_name
                elif 'bias' in col_lower and 'relative' not in col_lower:
                    # Check if it might be relative bias with different name
                    bias_col = col_name
            
            # If labcode column not found, use first column
            if labcode_col is None and len(df.columns) > 0:
                labcode_col = df.columns[0]
            
            if labcode_col is not None and bias_col is not None:
                # Process each lab in this file
                for idx, row in df.iterrows():
                    lab = str(row[labcode_col]).strip()
                    if not lab or pd.isna(lab):
                        continue
                    
                    bias_value = row[bias_col]
                    if not pd.isna(bias_value):
                        try:
                            # Convert to float and take absolute value
                            bias_abs = abs(float(bias_value))
                            lab_bias_data[lab].append(bias_abs)
                            lab_file_count[lab] += 1
                        except (ValueError, TypeError):
                            continue
                        
        except Exception as e:
            print(f"Error processing file {os.path.basename(file_path)}: {e}")
    
    # Calculate bias deviation index (mean of absolute relative bias) and variance for each lab
    lab_bias_stats = {}
    
    for lab, bias_values in lab_bias_data.items():
        if len(bias_values) > 0:
            bias_mean = np.mean(bias_values)
            bias_variance = np.var(bias_values)
            bias_std = np.std(bias_values)
            lab_bias_stats[lab] = {
                'bias_mean': bias_mean,
                'bias_variance': bias_variance,
                'bias_std': bias_std,
                'n_projects': len(bias_values),
                'total_participation': lab_file_count[lab]
            }
    
    # Convert to DataFrame and sort by bias deviation index (mean absolute bias)
    if lab_bias_stats:
        rows = []
        for lab, stats in lab_bias_stats.items():
            rows.append({
                'labcode': lab,
                f'bias_mean_{year}': stats['bias_mean'],
                f'bias_variance_{year}': stats['bias_variance'],
                f'bias_std_{year}': stats['bias_std'],
                f'n_projects_{year}': stats['n_projects'],
                f'total_participation_{year}': stats['total_participation']
            })
        
        df = pd.DataFrame(rows)
        
        # Sort by bias mean (lower is better)
        df = df.sort_values(f'bias_mean_{year}', ascending=True).reset_index(drop=True)
    
        # Calculate competitive ranking (skip ties, lower bias mean = better rank)
        current_rank = 1
        ranks = []
        prev_mean = None
    
        for mean in df[f'bias_mean_{year}']:
            if prev_mean is None or mean != prev_mean:
                current_rank = len(ranks) + 1
            ranks.append(current_rank)
            prev_mean = mean
    
        df[f'rank_{year}'] = ranks
        
        # Mark special laboratories
        df['is_special'] = False
        df['special_type'] = 'normal'
        
        if year in year_special_labs:
            for special_lab in year_special_labs[year]:
                special_mask = df['labcode'].astype(str).str.strip().str.lower() == special_lab.lower()
                if special_mask.any():
                    df.loc[special_mask, 'is_special'] = True
                    df.loc[special_mask, 'special_type'] = 'year_special'
                    print(f"  Found special laboratory: {df.loc[special_mask, 'labcode'].iloc[0]}")
        
        return df, len(all_files), year
    else:
        return None, 0, year

def create_year_specific_plots(year_dfs):
    """
    Create individual scatter plots for each year
    """
    # Create output folder
    output_folder = "labcode_bias_analysis_charts"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Set colors for special labs by year
    year_colors = {
        2021: {'special': 'red'},
        2022: {'special': 'green'},
        2023: {'special': 'blue'},
        2024: {'special': 'orange'}
    }
    
    for df, file_count, year in year_dfs:
        if df is None:
            continue
        
        print(f"\nCreating chart for {year}...")
        
        # Prepare data - filter labs with bias within 0-50 range
        df = df.copy()
        
        # Count labs before filtering
        total_labs = len(df)
        
        # Filter labs with bias mean within 0-50
        bias_col = f'bias_mean_{year}'
        df_filtered = df[df[bias_col] <= 50].copy()
        
        if len(df_filtered) == 0:
            print(f"  No labs with bias within 0-50 range for {year}")
            continue
        
        print(f"  Displaying {len(df_filtered)}/{total_labs} labs with bias ≤ 50")
        
        # Sort by bias mean (lower is better)
        df_filtered = df_filtered.sort_values(bias_col, ascending=True).reset_index(drop=True)
        df_filtered['x'] = range(len(df_filtered))
        
        # Separate special and regular labs
        special_df = df_filtered[df_filtered['is_special']].copy()
        regular_df = df_filtered[~df_filtered['is_special']].copy()
        
        # Create scatter plot with error bars
        plt.figure(figsize=(15, 8))
        
        # Plot regular labs
        if len(regular_df) > 0:
            plt.errorbar(regular_df['x'], regular_df[bias_col], 
                        yerr=regular_df[f'bias_std_{year}'],  # Use standard deviation as error bars
                        fmt='o', 
                        markersize=6,  # Smaller size for regular labs
                        color='skyblue',
                        alpha=0.7,
                        ecolor='lightgray',
                        elinewidth=0.5,
                        capsize=2,
                        zorder=5,
                        label='Regular Labs')
        
        # Plot special labs
        if len(special_df) > 0:
            special_color = year_colors.get(year, {}).get('special', 'red')
            plt.errorbar(special_df['x'], special_df[bias_col], 
                        yerr=special_df[f'bias_std_{year}'],  # Use standard deviation as error bars
                        fmt='o', 
                        markersize=12,  # Larger size for special labs
                        color=special_color,
                        alpha=0.9,
                        ecolor='gray',
                        elinewidth=1,
                        capsize=3,
                        zorder=10,
                        label='Special Labs')
        
        # Set x-axis labels - show all labels, small font
        plt.xticks(df_filtered['x'], df_filtered['labcode'], rotation=90, ha='right', fontsize=4)
        
        # Set axis labels
        plt.xlabel('Laboratory Code (Sorted by Bias Deviation Index)', fontsize=12, fontweight='bold')
        plt.ylabel(f'Bias Deviation Index ({year})', fontsize=12, fontweight='bold')
        
        # Add grid
        plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
        
        # Adjust axis ranges
        plt.xlim(-1, len(df_filtered))
        plt.ylim(0, 50)  # Fixed y-axis range 0-50
        
        # Add labels for special laboratories
        for _, row in special_df.iterrows():
            # Determine label position
            text_offset = 15 if row[bias_col] < 40 else -15
            
            plt.annotate(f"{row['labcode']}",
                        xy=(row['x'], row[bias_col]),
                        xytext=(0, text_offset),
                        textcoords='offset points',
                        ha='center',
                        fontsize=10,
                        fontweight='bold',
                        color='black',
                        bbox=dict(boxstyle='round,pad=0.3', 
                                 facecolor=year_colors.get(year, {}).get('special', 'yellow'), 
                                 alpha=0.8, 
                                 edgecolor='black'))
        
        # Add title and statistics
        avg_bias = df_filtered[bias_col].mean()
        min_bias = df_filtered[bias_col].min()
        max_bias = df_filtered[bias_col].max()
        avg_variance = df_filtered[f'bias_variance_{year}'].mean()
        avg_projects = df_filtered[f'n_projects_{year}'].mean()
        
        # Calculate statistics for all labs (including those > 50)
        avg_bias_all = df[bias_col].mean()
        max_bias_all = df[bias_col].max()
        outliers_count = total_labs - len(df_filtered)
        
        # Get special laboratory information
        special_info = ""
        if not special_df.empty:
            for _, row in special_df.iterrows():
                special_info += (f"{row['labcode']}: Rank {row[f'rank_{year}']}, "
                               f"Bias: {row[bias_col]:.3f}±{row[f'bias_std_{year}']:.3f}, "
                               f"Projects: {row[f'n_projects_{year}']}; ")
        
        stats_text = (f"Displayed Labs: {len(df_filtered)}/{total_labs} | Outliers (>50): {outliers_count} | "
                     f"Avg Bias (shown): {avg_bias:.3f} | Min: {min_bias:.3f} | Max (shown): {max_bias:.3f} | "
                     f"Avg Bias (all): {avg_bias_all:.3f} | Max (all): {max_bias_all:.3f}")
        
        title_text = f'Laboratory Bias Deviation Analysis - {year}\n{stats_text}'
        if special_info:
            title_text += f"\nSpecial Labs: {special_info}"
        
        plt.title(title_text, fontsize=14, fontweight='bold', pad=25)
        
        # Add horizontal line at bias=50 for reference
        plt.axhline(y=50, color='red', linestyle='--', alpha=0.3, linewidth=1, label='Upper Limit (50)')
        
        # Add legend
        plt.legend(loc='upper right')
        
        # Adjust layout to make space for x-axis labels
        plt.tight_layout(rect=[0.03, 0.05, 0.97, 0.95])
        
        # Save image
        output_file = f"{output_folder}/labcode_bias_deviation_{year}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Chart saved: {output_file}")
        
        # Save detailed data to CSV (both filtered and all data)
        csv_file = f"{output_folder}/labcode_bias_deviation_{year}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"Data saved: {csv_file}")
        
        # Also save filtered data
        csv_filtered_file = f"{output_folder}/labcode_bias_deviation_{year}_filtered.csv"
        df_filtered.to_csv(csv_filtered_file, index=False, encoding='utf-8-sig')
        print(f"Filtered data saved: {csv_filtered_file}")

def create_comparison_plot(year_dfs):
    """
    Create year comparison plot
    """
    print("\nCreating year comparison plot...")
    
    # Collect data for each year
    comparison_data = []
    
    for df, file_count, year in year_dfs:
        if df is not None and len(df) > 0:
            # Statistics
            total_labs = len(df)
            avg_bias = df[f'bias_mean_{year}'].mean()
            min_bias = df[f'bias_mean_{year}'].min()
            max_bias = df[f'bias_mean_{year}'].max()
            avg_variance = df[f'bias_variance_{year}'].mean()
            avg_projects = df[f'n_projects_{year}'].mean()
            
            # Special laboratory information
            special_labs = df[df['is_special']]
            special_info = ""
            if not special_labs.empty:
                for _, row in special_labs.iterrows():
                    special_info += (f"{row['labcode']}(Bias:{row[f'bias_mean_{year}']:.3f}±{row[f'bias_std_{year}']:.3f}) ")
            
            comparison_data.append({
                'Year': year,
                'Total Projects': file_count,
                'Total Labs': total_labs,
                'Avg Bias': avg_bias,
                'Min Bias': min_bias,
                'Max Bias': max_bias,
                'Avg Variance': avg_variance,
                'Avg Projects per Lab': avg_projects,
                'Special Labs': special_info.strip()
            })
    
    if not comparison_data:
        print("Not enough data to create comparison plot")
        return
    
    # Convert to DataFrame
    comp_df = pd.DataFrame(comparison_data)
    
    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Chart 1: Total labs and projects
    ax1 = axes[0, 0]
    x_pos = np.arange(len(comp_df))
    width = 0.35
    
    bars1 = ax1.bar(x_pos - width/2, comp_df['Total Projects'], width, 
                   label='Total Projects', alpha=0.8, color='skyblue')
    bars2 = ax1.bar(x_pos + width/2, comp_df['Total Labs'], width, 
                   label='Total Labs', alpha=0.8, color='lightcoral')
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax1.set_title('Projects and Labs by Year', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(comp_df['Year'])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    # Chart 2: Average bias
    ax2 = axes[0, 1]
    bars3 = ax2.bar(comp_df['Year'], comp_df['Avg Bias'], 
                   alpha=0.7, color='orange', yerr=comp_df['Avg Variance'])
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Avg Bias Deviation Index', fontsize=12, fontweight='bold')
    ax2.set_title('Average Bias Deviation by Year', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    for i, (year, avg_bias) in enumerate(zip(comp_df['Year'], comp_df['Avg Bias'])):
        ax2.text(i, avg_bias + 0.01, f'{avg_bias:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Chart 3: Minimum bias (best performance)
    ax3 = axes[1, 0]
    bars4 = ax3.bar(comp_df['Year'], comp_df['Min Bias'], 
                   alpha=0.7, color='green')
    
    ax3.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Minimum Bias (Best)', fontsize=12, fontweight='bold')
    ax3.set_title('Best Laboratory Performance by Year', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    for i, (year, min_bias) in enumerate(zip(comp_df['Year'], comp_df['Min Bias'])):
        ax3.text(i, min_bias + 0.005, f'{min_bias:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Chart 4: Special labs information
    ax4 = axes[1, 1]
    ax4.axis('off')  # Hide axes
    
    # Create table to display special labs
    table_data = []
    for _, row in comp_df.iterrows():
        table_data.append([row['Year'], row['Special Labs']])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Year', 'Special Labs (Bias±Std)'],
                     cellLoc='left',
                     loc='center',
                     colWidths=[0.2, 0.8])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Set table style
    for i in range(len(table_data) + 1):
        for j in range(2):
            cell = table[i, j]
            cell.set_edgecolor('black')
            if i == 0:
                cell.set_facecolor('#DDDDDD')
                cell.set_text_props(weight='bold')
    
    ax4.set_title('Special Laboratory Bias Performance', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save comparison plot
    output_folder = "labcode_bias_analysis_charts"
    output_file = f"{output_folder}/labcode_bias_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Comparison plot saved: {output_file}")
    
    # Save comparison data
    comp_csv = f"{output_folder}/labcode_bias_comparison.csv"
    comp_df.to_csv(comp_csv, index=False, encoding='utf-8-sig')
    print(f"Comparison data saved: {comp_csv}")

def create_special_labs_trend(year_dfs):
    """
    Create trend chart for special laboratories
    """
    print("\nCreating special labs trend chart...")
    
    # Special labs by year
    special_labs_by_year = {
        2021: '211',
        2022: '8', 
        2023: '43',
        2024: '5'
    }
    
    # Collect data
    trend_data = []
    
    for df, file_count, year in year_dfs:
        if df is not None and year in special_labs_by_year:
            special_lab_code = special_labs_by_year[year]
            special_row = df[df['labcode'].astype(str).str.strip().str.lower() == special_lab_code.lower()]
            
            if not special_row.empty:
                row = special_row.iloc[0]
                trend_data.append({
                    'Year': year,
                    'Labcode': row['labcode'],
                    'Bias Mean': row[f'bias_mean_{year}'],
                    'Bias Std': row[f'bias_std_{year}'],
                    'Rank': row[f'rank_{year}'],
                    'Projects': row[f'n_projects_{year}'],
                    'Total Projects': file_count
                })
    
    if len(trend_data) < 2:
        print("Not enough special lab data to create trend chart")
        return
    
    trend_df = pd.DataFrame(trend_data)
    
    # Create trend chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Chart 1: Bias trend with error bars
    years = trend_df['Year']
    labcodes = trend_df['Labcode']
    bias_means = trend_df['Bias Mean']
    bias_stds = trend_df['Bias Std']
    
    colors = ['red', 'green', 'blue', 'orange']
    
    x_pos = range(len(years))
    
    for i, (year, labcode, bias_mean, bias_std, color) in enumerate(zip(years, labcodes, bias_means, bias_stds, colors)):
        ax1.bar(i, bias_mean, color=color, alpha=0.7, edgecolor='black', yerr=bias_std, capsize=5)
        ax1.text(i, bias_mean + bias_std + 0.01, f'{labcode}', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Bias Deviation Index', fontsize=12, fontweight='bold')
    ax1.set_title('Special Labs: Bias Deviation Trend', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(years)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bias_mean, bias_std) in enumerate(zip(bias_means, bias_stds)):
        ax1.text(i, bias_mean/2, f'{bias_mean:.3f}±{bias_std:.3f}', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    
    # Chart 2: Ranking trend
    ranks = trend_df['Rank']
    
    ax2.plot(x_pos, ranks, marker='o', markersize=10, 
             linewidth=2, color='purple', alpha=0.7)
    
    for i, (year, labcode, rank, bias_mean) in enumerate(zip(years, labcodes, ranks, bias_means)):
        ax2.text(i, rank + 0.5, f'{labcode}: Rank {int(rank)} ({bias_mean:.3f})', 
                ha='center', va='bottom', fontsize=10)
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Rank', fontsize=12, fontweight='bold')
    ax2.set_title('Special Labs: Ranking Trend', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(years)
    ax2.invert_yaxis()  # Lower rank is better, so invert y-axis
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save trend chart
    output_folder = "labcode_bias_analysis_charts"
    output_file = f"{output_folder}/special_labs_bias_trend.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Special labs trend chart saved: {output_file}")
    
    # Save trend data
    trend_csv = f"{output_folder}/special_labs_bias_trend.csv"
    trend_df.to_csv(trend_csv, index=False, encoding='utf-8-sig')
    print(f"Trend data saved: {trend_csv}")

def main():
    """
    Main function: Analyze laboratory bias deviation for 2021-2024
    """
    print("="*70)
    print("Laboratory Bias Deviation Analysis (2021-2024)")
    print("Bias Deviation Index = Mean of absolute Relative Bias values")
    print("Error bars represent ±1 standard deviation")
    print("="*70)
    print("Special Laboratories by Year:")
    print("  2021: Lab 211")
    print("  2022: Lab 8") 
    print("  2023: Lab 43")
    print("  2024: Lab 5")
    print("="*70)
    
    # Years to analyze
    years = [2021, 2022, 2023, 2024]
    
    # Analyze each year
    year_dfs = []
    
    for year in years:
        print(f"\n{'='*40}")
        print(f"Analyzing {year}...")
        print(f"{'='*40}")
        
        df, file_count, year_val = analyze_single_year(year)
        year_dfs.append((df, file_count, year_val))
        
        if df is not None:
            print(f"{year_val} Statistics:")
            print(f"  Total Projects: {file_count}")
            print(f"  Participating Labs: {len(df)}")
            print(f"  Avg Bias Deviation: {df[f'bias_mean_{year_val}'].mean():.4f}")
            print(f"  Min Bias (Best): {df[f'bias_mean_{year_val}'].min():.4f}")
            print(f"  Max Bias (Worst): {df[f'bias_mean_{year_val}'].max():.4f}")
            print(f"  Avg Variance: {df[f'bias_variance_{year_val}'].mean():.4f}")
            print(f"  Avg Projects per Lab: {df[f'n_projects_{year_val}'].mean():.1f}")
            
            # Display special laboratories
            special = df[df['is_special']]
            if not special.empty:
                print(f"  Special Laboratories:")
                for _, row in special.iterrows():
                    rank = row[f'rank_{year_val}']
                    bias_mean = row[f'bias_mean_{year_val}']
                    bias_std = row[f'bias_std_{year_val}']
                    projects = row[f'n_projects_{year_val}']
                    print(f"    {row['labcode']}: Rank {rank}, "
                          f"Bias: {bias_mean:.4f}±{bias_std:.4f}, "
                          f"Projects: {projects}/{file_count} ({projects/file_count*100:.1f}%)")
    
    # Create individual charts for each year
    create_year_specific_plots(year_dfs)
    
    # Create year comparison plot
    create_comparison_plot(year_dfs)
    
    # Create special labs trend chart
    create_special_labs_trend(year_dfs)
    
    print(f"\n{'='*70}")
    print("Analysis Complete!")
    print(f"All charts saved to 'labcode_bias_analysis_charts' folder")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()