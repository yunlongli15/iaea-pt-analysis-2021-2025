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
    Analyze laboratory performance for a single year
    """
    # Set special labs for each year
    year_special_labs = {
        2021: ['211', 'lab211', 'labcode211'],
        2022: ['8', 'lab8', 'labcode8'],
        2023: ['43', 'lab43', 'labcode43'],
        2024: ['5', 'lab5', 'labcode5'],
        2025: ['15', 'lab15', 'labcode15']
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
    
    # Count laboratory A-count (accepted results)
    lab_a_count = defaultdict(int)
    lab_total_participation = defaultdict(int)  # Also track total participation
    
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
            
            # Find labcode column and score column
            labcode_col = None
            score_col = None
            
            # Find labcode column
            for col_name in df.columns:
                if 'labcode' in str(col_name).lower():
                    labcode_col = col_name
                    break
            
            # Find score column (Final Score or Z-Score Evaluation)
            for col_name in df.columns:
                if 'final score' in str(col_name).lower() or 'final' in str(col_name).lower() or 'z-score evaluation' in str(col_name).lower():
                    score_col = col_name
                    print(f"    Found score column: {score_col}")
                    break
            
            # If labcode column not found, use first column
            if labcode_col is None and len(df.columns) > 0:
                labcode_col = df.columns[0]
            
            if labcode_col is not None:
                # Process each lab in this file
                for idx, row in df.iterrows():
                    lab = str(row[labcode_col]).strip()
                    if not lab or pd.isna(lab):
                        continue
                    
                    # Count total participation
                    lab_total_participation[lab] += 1
                    if lab == '15':
                        print('lab15 participation count +1')
                    
                    # Count A's if score column exists and value is 'A'
                    if score_col is not None and score_col in row:
                        score = str(row[score_col]).strip().upper()
                        if score == 'A':
                            lab_a_count[lab] += 1
                        if lab == '15':
                            print('lab15 A count +1')
                        if lab == '537':
                            print('lab537 A count +1'+file_path)
                        
        except Exception as e:
            print(f"Error processing file {os.path.basename(file_path)}: {e}")
    
    # Convert to DataFrame and sort by A-count
    if lab_a_count:
        df = pd.DataFrame(list(lab_a_count.items()), 
                         columns=['labcode', f'a_count_{year}'])
        
        # Add total participation count
        df[f'total_count_{year}'] = df['labcode'].map(lab_total_participation)
        
        # Calculate A-rate (percentage)
        df[f'a_rate_{year}'] = df.apply(
            lambda row: (row[f'a_count_{year}'] / row[f'total_count_{year}']) * 100 
            if row[f'total_count_{year}'] > 0 else 0, 
            axis=1
        )
        
        # 先排序
        df = df.sort_values(f'a_count_{year}', ascending=False).reset_index(drop=True)
    
        # 计算竞争排名（并列时跳过名次）
        current_rank = 1
        ranks = []
        prev_count = None
    
        for count in df[f'a_count_{year}']:
            if prev_count is None or count != prev_count:
                current_rank = len(ranks) + 1
            ranks.append(current_rank)
            prev_count = count
    
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
    output_folder = "labcode_analysis_charts"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Set colors for special labs by year
    year_colors = {
        2021: {'special': 'red'},
        2022: {'special': 'green'},
        2023: {'special': 'blue'},
        2024: {'special': 'orange'},
        2025: {'special': 'orange'}
    }
    
    for df, file_count, year in year_dfs:
        if df is None:
            continue
        
        print(f"\nCreating chart for {year}...")
        
        # Prepare data
        df = df.copy()
        df['x'] = range(len(df))
        
        # Set colors and sizes
        df['color'] = np.where(df['is_special'], 
                              year_colors.get(year, {}).get('special', 'red'), 
                              'skyblue')
        df['size'] = np.where(df['is_special'], 60, 10)
        
        # Create scatter plot
        plt.figure(figsize=(18, 8))
        
        # Plot scatter points (A-count on y-axis)
        plt.scatter(df['x'], df[f'a_count_{year}'], 
                   s=df['size'], 
                   c=df['color'], 
                   alpha=0.7, 
                   edgecolors='black', 
                   linewidths=0.5,
                   zorder=5)
        
        # Set x-axis labels - show all labels, small font
        plt.xticks(df['x'], df['labcode'], rotation=90, ha='right', fontsize=4)
        
        # Set axis labels
        plt.xlabel('Laboratory Code', fontsize=12, fontweight='bold')
        plt.ylabel(f'Number of Projects with A (Accepted) ({year})', fontsize=12, fontweight='bold')
        
        # Add grid
        plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
        
        # Adjust axis ranges
        plt.xlim(-1, len(df))
        y_max = df[f'a_count_{year}'].max()
        plt.ylim(0, y_max * 1.05)
        
        # Add labels for special laboratories
        special_labs = df[df['is_special']]
        for _, row in special_labs.iterrows():
            # Determine label position
            text_offset = 15 if row[f'a_count_{year}'] < y_max * 0.8 else -15
            
            plt.annotate(f"{row['labcode']}",
                        xy=(row['x'], row[f'a_count_{year}']),
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
        total_labs = len(df)
        avg_a_count = df[f'a_count_{year}'].mean()
        max_a_count = df[f'a_count_{year}'].max()
        avg_a_rate = df[f'a_rate_{year}'].mean()
        
        # Get special laboratory information
        special_info = ""
        if not special_labs.empty:
            for _, row in special_labs.iterrows():
                special_info += f"{row['labcode']}: Rank {row[f'rank_{year}']}, {row[f'a_count_{year}']} A's; "
        
        stats_text = f"Total Labs: {total_labs} | Avg A's: {avg_a_count:.1f} | Max A's: {max_a_count} | Avg A-rate: {avg_a_rate:.1f}%"
        title_text = f'Laboratory Performance Analysis - {year}\n{stats_text}'
        if special_info:
            title_text += f"\nSpecial Labs: {special_info}"
        
        plt.title(title_text, fontsize=14, fontweight='bold', pad=25)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='skyblue', alpha=0.7, edgecolor='black', label='Regular Labs'),
            Patch(facecolor=year_colors.get(year, {}).get('special', 'red'), alpha=0.7, edgecolor='black', label='Special Labs')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Adjust layout to make space for x-axis labels
        plt.tight_layout(rect=[0.03, 0.05, 0.97, 0.95])
        
        # Save image
        output_file = f"{output_folder}/labcode_a_count_{year}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Chart saved: {output_file}")
        
        # Save detailed data to CSV
        csv_file = f"{output_folder}/labcode_a_count_{year}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"Data saved: {csv_file}")

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
            avg_a_count = df[f'a_count_{year}'].mean()
            max_a_count = df[f'a_count_{year}'].max()
            min_a_count = df[f'a_count_{year}'].min()
            avg_a_rate = df[f'a_rate_{year}'].mean()
            
            # Special laboratory information
            special_labs = df[df['is_special']]
            special_info = ""
            if not special_labs.empty:
                for _, row in special_labs.iterrows():
                    special_info += f"{row['labcode']}({row[f'a_count_{year}']}A/{row[f'total_count_{year}']}P={row[f'a_rate_{year}']:.1f}%) "
            
            comparison_data.append({
                'Year': year,
                'Total Projects': file_count,
                'Total Labs': total_labs,
                'Avg A Count': avg_a_count,
                'Max A Count': max_a_count,
                'Min A Count': min_a_count,
                'Avg A Rate': avg_a_rate,
                'Special Labs': special_info.strip()
            })
    
    if not comparison_data:
        print("Not enough data to create comparison plot")
        return
    
    # Convert to DataFrame
    comp_df = pd.DataFrame(comparison_data)
    
    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Chart 1: Project and lab counts
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
    
    # Chart 2: Average A count
    ax2 = axes[0, 1]
    bars3 = ax2.bar(comp_df['Year'], comp_df['Avg A Count'], 
                   alpha=0.7, color='orange')
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Avg A Count per Lab', fontsize=12, fontweight='bold')
    ax2.set_title('Average A Count by Year', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    for bar in bars3:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=10)
    
    # Chart 3: Maximum A count
    ax3 = axes[1, 0]
    bars4 = ax3.bar(comp_df['Year'], comp_df['Max A Count'], 
                   alpha=0.7, color='green')
    
    ax3.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Max A Count', fontsize=12, fontweight='bold')
    ax3.set_title('Maximum A Count by Year', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    for bar in bars4:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # Chart 4: Special labs information
    ax4 = axes[1, 1]
    ax4.axis('off')  # Hide axes
    
    # Create table to display special labs
    table_data = []
    for _, row in comp_df.iterrows():
        table_data.append([row['Year'], row['Special Labs']])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Year', 'Special Labs (A/Total=%A)'],
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
    
    ax4.set_title('Special Laboratory Performance', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save comparison plot
    output_folder = "labcode_analysis_charts"
    output_file = f"{output_folder}/labcode_a_count_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Comparison plot saved: {output_file}")
    
    # Save comparison data
    comp_csv = f"{output_folder}/labcode_a_count_comparison.csv"
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
        2024: '5',
        2025: '15'
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
                    'A Count': row[f'a_count_{year}'],
                    'Total Count': row[f'total_count_{year}'],
                    'A Rate': row[f'a_rate_{year}'],
                    'Rank': row[f'rank_{year}'],
                    'Total Projects': file_count
                })
    
    if len(trend_data) < 2:
        print("Not enough special lab data to create trend chart")
        return
    
    trend_df = pd.DataFrame(trend_data)
    
    # Create trend chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Chart 1: A count trend
    years = trend_df['Year']
    labcodes = trend_df['Labcode']
    a_counts = trend_df['A Count']
    a_rates = trend_df['A Rate']
    
    colors = ['red', 'green', 'blue', 'orange']
    
    for i, (year, labcode, a_count, a_rate, color) in enumerate(zip(years, labcodes, a_counts, a_rates, colors)):
        ax1.bar(i, a_count, color=color, alpha=0.7, edgecolor='black')
        ax1.text(i, a_count + 0.5, f'{labcode}', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
        # Add A-rate as text above bar
        ax1.text(i, a_count/2, f'{a_rate:.1f}%', 
                ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Projects with A', fontsize=12, fontweight='bold')
    ax1.set_title('Special Labs: A Count Trend', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(years)))
    ax1.set_xticklabels(years)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels for A count
    for i, a_count in enumerate(a_counts):
        ax1.text(i, a_count/2, f'{int(a_count)}', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    
    # Chart 2: Ranking trend
    ranks = trend_df['Rank']
    
    ax2.plot(range(len(years)), ranks, marker='o', markersize=10, 
             linewidth=2, color='purple', alpha=0.7)
    
    for i, (year, labcode, rank, a_rate) in enumerate(zip(years, labcodes, ranks, a_rates)):
        ax2.text(i, rank + 0.5, f'{labcode}: Rank {int(rank)} ({a_rate:.1f}%)', 
                ha='center', va='bottom', fontsize=9)
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Rank', fontsize=12, fontweight='bold')
    ax2.set_title('Special Labs: Ranking Trend', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(years)))
    ax2.set_xticklabels(years)
    ax2.invert_yaxis()  # Lower rank is better, so invert y-axis
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save trend chart
    output_folder = "labcode_analysis_charts"
    output_file = f"{output_folder}/special_labs_a_trend.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Special labs trend chart saved: {output_file}")

def main():
    """
    Main function: Analyze laboratory A-count performance for 2021-2024
    """
    print("="*60)
    print("Laboratory A-Count Performance Analysis (2021-2025)")
    print("="*60)
    print("Special Laboratories by Year:")
    print("  2021: Lab 211")
    print("  2022: Lab 8") 
    print("  2023: Lab 43")
    print("  2024: Lab 5")
    print("  2025: Lab 15")
    print("="*60)
    
    # Years to analyze
    years = [2021, 2022, 2023, 2024, 2025]
    
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
            print(f"  Avg A's per Lab: {df[f'a_count_{year_val}'].mean():.1f}")
            print(f"  Max A's: {df[f'a_count_{year_val}'].max()}")
            print(f"  Avg A-rate: {df[f'a_rate_{year_val}'].mean():.1f}%")
            
            # Display special laboratories
            special = df[df['is_special']]
            if not special.empty:
                print(f"  Special Laboratories:")
                for _, row in special.iterrows():
                    rank = row[f'rank_{year_val}']
                    a_count = row[f'a_count_{year_val}']
                    total_count = row[f'total_count_{year_val}']
                    a_rate = row[f'a_rate_{year_val}']
                    print(f"    {row['labcode']}: Rank {rank}, {a_count}/{total_count} A's ({a_rate:.1f}%)")
    
    # Create individual charts for each year
    create_year_specific_plots(year_dfs)
    
    # Create year comparison plot
    create_comparison_plot(year_dfs)
    
    # Create special labs trend chart
    create_special_labs_trend(year_dfs)
    
    print(f"\n{'='*60}")
    print("Analysis Complete!")
    print(f"All charts saved to 'labcode_analysis_charts' folder")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()