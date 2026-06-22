import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

def analyze_year_projects_by_difficulty(year, difficulty_min, difficulty_max, difficulty_label):
    """
    Analyze projects by difficulty range for a specific year
    """
    print(f"\nAnalyzing {difficulty_label} projects for {year}...")
    
    # Special labs for each year
    special_labs_by_year = {
        2021: ['211', 'lab211', 'labcode211'],
        2022: ['8', 'lab8', 'labcode8'],
        2023: ['43', 'lab43', 'labcode43'],
        2024: ['5', 'lab5', 'labcode5']
    }
    
    # Read difficulty file for the year
    difficulty_file = f"{year}_Project_Difficulty_Analysis_Results.csv"
    
    if not os.path.exists(difficulty_file):
        print(f"Warning: Difficulty file '{difficulty_file}' not found. Skipping {year}.")
        return None, None, 0, None
    
    try:
        # Try different encodings
        try:
            df_difficulty = pd.read_csv(difficulty_file, encoding='utf-8-sig')
        except:
            try:
                df_difficulty = pd.read_csv(difficulty_file, encoding='gbk')
            except:
                df_difficulty = pd.read_csv(difficulty_file, encoding='latin1')
    except Exception as e:
        print(f"Error reading difficulty file for {year}: {e}")
        return None, None, 0, None
    
    print(f"  Read difficulty file: {len(df_difficulty)} projects")
    
    # Filter projects by difficulty range
    if difficulty_max is not None:
        filtered_df = df_difficulty[(df_difficulty['Difficulty Coefficient'] >= difficulty_min) & 
                                   (df_difficulty['Difficulty Coefficient'] < difficulty_max)]
    else:
        filtered_df = df_difficulty[df_difficulty['Difficulty Coefficient'] >= difficulty_min]
    
    if len(filtered_df) == 0:
        print(f"  No {difficulty_label} projects found for {year}")
        return None, None, 0, None
    
    print(f"  Found {len(filtered_df)} {difficulty_label} projects")
    
    # Check folder path
    folder_path = f"merged_labcode_tables_{year}"
    if not os.path.exists(folder_path):
        print(f"Warning: Folder '{folder_path}' not found. Skipping {year}.")
        return None, None, 0, None
    
    # Count laboratory project detection
    lab_detection_count = defaultdict(int)
    
    for _, row in filtered_df.iterrows():
        file_name = row['File Name']
        file_path = os.path.join(folder_path, file_name)
        
        if not os.path.exists(file_path):
            # Try to find similar file
            possible_files = glob.glob(f"{folder_path}/*{file_name.split('_')[2] if len(file_name.split('_')) > 2 else ''}*")
            if possible_files:
                file_path = possible_files[0]
            else:
                continue
        
        try:
            # Read file
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # Find labcode column and score column
            labcode_col = None
            score_col = None
            
            for col_name in df.columns:
                col_lower = str(col_name).lower()
                if 'labcode' in col_lower:
                    labcode_col = col_name
                elif 'final score' in col_lower or 'z-score evaluation' in col_lower:
                    score_col = col_name
            
            # If no labcode column found, use first column
            if labcode_col is None and len(df.columns) > 0:
                labcode_col = df.columns[0]
            
            if labcode_col is not None:
                # Check each lab's score
                for _, row_data in df.iterrows():
                    lab = str(row_data[labcode_col]).strip()
                    if not lab or pd.isna(lab):
                        continue
                    
                    # Check if score is 'A'
                    if score_col is not None and score_col in row_data:
                        score = str(row_data[score_col]).strip().upper()
                        if score == 'A':
                            lab_detection_count[lab] += 1
                    else:
                        # If no score column, count all participating labs
                        lab_detection_count[lab] += 1
                        
        except Exception as e:
            print(f"  Error processing file {file_name}: {e}")
    
    # Convert to DataFrame and sort
    if lab_detection_count:
        result_df = pd.DataFrame(list(lab_detection_count.items()), 
                                columns=['labcode', f'{difficulty_label.lower().replace(" ", "_")}_count_{year}'])
        
        # Add project count for reference
        result_df[f'total_{difficulty_label.lower().replace(" ", "_")}_projects_{year}'] = len(filtered_df)
        
        # Sort by count
        count_col = f'{difficulty_label.lower().replace(" ", "_")}_count_{year}'
        result_df = result_df.sort_values(count_col, ascending=False).reset_index(drop=True)
        
        # Calculate competitive ranking (skip ties)
        current_rank = 1
        ranks = []
        prev_count = None
        
        for count in result_df[count_col]:
            if prev_count is None or count != prev_count:
                current_rank = len(ranks) + 1
            ranks.append(current_rank)
            prev_count = count
        
        result_df[f'{difficulty_label.lower().replace(" ", "_")}_rank_{year}'] = ranks
        
        # Calculate detection rate
        result_df[f'{difficulty_label.lower().replace(" ", "_")}_rate_{year}'] = (result_df[count_col] / 
                                                                                result_df[f'total_{difficulty_label.lower().replace(" ", "_")}_projects_{year}']) * 100
        
        # Mark special laboratories
        result_df['is_special'] = False
        
        if year in special_labs_by_year:
            for special_lab in special_labs_by_year[year]:
                special_mask = result_df['labcode'].astype(str).str.strip().str.lower() == special_lab.lower()
                if special_mask.any():
                    result_df.loc[special_mask, 'is_special'] = True
                    print(f"  Found special laboratory: {result_df.loc[special_mask, 'labcode'].iloc[0]}")
        
        # Get special lab info
        special_lab_info = None
        special_rows = result_df[result_df['is_special']]
        if not special_rows.empty:
            special_lab_info = special_rows.iloc[0]
        
        return result_df, len(filtered_df), year, special_lab_info, difficulty_label
    else:
        return None, 0, year, None, difficulty_label

def create_year_specific_charts(year_dfs, output_folder, difficulty_label):
    """
    Create individual charts for each year
    """
    print(f"\nCreating year-specific charts for {difficulty_label} projects...")
    
    for result_df, project_count, year, special_lab_info, label in year_dfs:
        if result_df is None or label != difficulty_label:
            continue
        
        print(f"  Creating chart for {year}...")
        
        # Prepare data for chart - filter out labs with 0 detection
        df = result_df.copy()
        count_col = f'{difficulty_label.lower().replace(" ", "_")}_count_{year}'
        
        # Filter to show only labs with at least 1 detection
        df = df[df[count_col] > 0].copy()
        
        if len(df) == 0:
            print(f"    No labs with detection for {year}")
            continue
        
        # Sort by detection count (already sorted, but ensure)
        df = df.sort_values(count_col, ascending=False).reset_index(drop=True)
        
        # Create x-axis positions for all labs
        df['x'] = range(len(df))
        
        # Set colors and sizes
        df['color'] = np.where(df['is_special'], 'red', 'skyblue')
        df['size'] = np.where(df['is_special'], 80, 40)
        
        # Create scatter plot
        plt.figure(figsize=(18, 8))  # Adjust width based on number of labs
        
        # Plot all labs
        plt.scatter(df['x'], df[count_col], 
                   s=df['size'], 
                   c=df['color'], 
                   alpha=0.7, 
                   edgecolors='black', 
                   linewidths=1,
                   zorder=5)
        
        # Set x-axis labels - show all lab codes
        plt.xticks(df['x'], df['labcode'], rotation=90, ha='right', fontsize=6)
        
        # Set axis labels
        plt.xlabel('Laboratory Code', fontsize=12, fontweight='bold')
        plt.ylabel(f'{difficulty_label} Projects Detected ({year})', fontsize=12, fontweight='bold')
        
        # Add grid
        plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
        
        # Adjust axis ranges
        plt.xlim(-1, len(df))
        y_max = df[count_col].max()
        plt.ylim(-0.5, y_max + 0.5)
        
        # Add horizontal line at max value
        plt.axhline(y=y_max, color='green', linestyle='--', alpha=0.5, linewidth=1, 
                   label=f'Max: {int(y_max)}')
        
        # Add title with statistics
        total_labs = len(df)
        avg_detection = df[count_col].mean()
        max_detection = df[count_col].max()
        min_detection = df[count_col].min()
        
        stats_text = (f"Total Labs with Detection: {total_labs} | {difficulty_label} Projects: {project_count} | "
                     f"Avg Detection: {avg_detection:.1f} | Max: {max_detection} | Min: {min_detection}")
        
        # Add special lab info to title if available
        title_text = f'{difficulty_label} Project Analysis - {year}\n{stats_text}'
        if special_lab_info is not None and special_lab_info['labcode'] in df['labcode'].values:
            rank_col = f'{difficulty_label.lower().replace(" ", "_")}_rank_{year}'
            rate_col = f'{difficulty_label.lower().replace(" ", "_")}_rate_{year}'
            title_text += (f"\nSpecial Lab: {special_lab_info['labcode']} - "
                          f"Rank {special_lab_info[rank_col]}, "
                          f"{special_lab_info[count_col]}/{project_count} "
                          f"({special_lab_info[rate_col]:.1f}%)")
        
        plt.title(title_text, fontsize=14, fontweight='bold', pad=25)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='skyblue', alpha=0.7, edgecolor='black', label='Regular Labs'),
            Patch(facecolor='red', alpha=0.7, edgecolor='black', label='Special Lab')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Add annotation for special lab if in display range
        if special_lab_info is not None and special_lab_info['labcode'] in df['labcode'].values:
            special_row = df[df['labcode'] == special_lab_info['labcode']].iloc[0]
            rank_col = f'{difficulty_label.lower().replace(" ", "_")}_rank_{year}'
            plt.annotate(f"Lab {special_row['labcode']}\nRank: {special_row[rank_col]}", 
                        xy=(special_row['x'], special_row[count_col]),
                        xytext=(0, 15), textcoords='offset points',
                        ha='center', fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        output_file = f"{output_folder}/{difficulty_label.lower().replace(' ', '_')}_analysis_{year}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Chart saved: {output_file}")
        
        # Save detailed data to CSV
        csv_file = f"{output_folder}/{difficulty_label.lower().replace(' ', '_')}_analysis_{year}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"    Data saved: {csv_file}")
        
        
def create_comparison_plot(year_dfs, output_folder, difficulty_label):
    """
    Create year comparison plot
    """
    print(f"\nCreating comparison plot for {difficulty_label} projects...")
    
    # Collect comparison data
    comparison_data = []
    
    for result_df, project_count, year, special_lab_info, label in year_dfs:
        if result_df is not None and label == difficulty_label:
            count_col = f'{difficulty_label.lower().replace(" ", "_")}_count_{year}'
            rank_col = f'{difficulty_label.lower().replace(" ", "_")}_rank_{year}'
            rate_col = f'{difficulty_label.lower().replace(" ", "_")}_rate_{year}'
            
            # General statistics
            total_labs = len(result_df)
            avg_detection = result_df[count_col].mean()
            max_detection = result_df[count_col].max()
            min_detection = result_df[count_col].min()
            
            # Special lab statistics
            special_labs = result_df[result_df['is_special']]
            special_info = ""
            if not special_labs.empty:
                for _, row in special_labs.iterrows():
                    special_info += (f"{row['labcode']}({row[count_col]}/"
                                   f"{project_count}={row[rate_col]:.1f}%) ")
            
            comparison_data.append({
                'Year': year,
                f'{difficulty_label} Projects': project_count,
                'Total Labs': total_labs,
                'Avg Detection': avg_detection,
                'Max Detection': max_detection,
                'Min Detection': min_detection,
                'Special Lab Info': special_info.strip()
            })
    
    if len(comparison_data) < 2:
        print(f"Not enough data for {difficulty_label} comparison plot")
        return
    
    # Create DataFrame
    comp_df = pd.DataFrame(comparison_data)
    
    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Chart 1: Projects and labs count
    ax1 = axes[0, 0]
    x_pos = np.arange(len(comp_df))
    width = 0.35
    
    bars1 = ax1.bar(x_pos - width/2, comp_df[f'{difficulty_label} Projects'], width, 
                   label=f'{difficulty_label} Projects', alpha=0.8, color='skyblue')
    bars2 = ax1.bar(x_pos + width/2, comp_df['Total Labs'], width, 
                   label='Labs Detecting', alpha=0.8, color='lightcoral')
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax1.set_title(f'{difficulty_label} Projects and Detecting Labs by Year', fontsize=14, fontweight='bold')
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
    
    # Chart 2: Average detection
    ax2 = axes[0, 1]
    bars3 = ax2.bar(comp_df['Year'], comp_df['Avg Detection'], 
                   alpha=0.7, color='orange')
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel(f'Avg {difficulty_label} Projects Detected', fontsize=12, fontweight='bold')
    ax2.set_title(f'Average {difficulty_label} Project Detection by Year', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    for bar in bars3:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=10)
    
    # Chart 3: Maximum detection
    ax3 = axes[1, 0]
    bars4 = ax3.bar(comp_df['Year'], comp_df['Max Detection'], 
                   alpha=0.7, color='green')
    
    ax3.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax3.set_ylabel(f'Max {difficulty_label} Projects Detected', fontsize=12, fontweight='bold')
    ax3.set_title(f'Maximum {difficulty_label} Project Detection by Year', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    for bar in bars4:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # Chart 4: Special labs information
    ax4 = axes[1, 1]
    ax4.axis('off')  # Hide axes
    
    # Create table for special labs info
    table_data = []
    for _, row in comp_df.iterrows():
        table_data.append([row['Year'], row['Special Lab Info']])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Year', f'Special Lab (Detected/Total=Rate%)'],
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
    
    ax4.set_title(f'Special Laboratory Performance on {difficulty_label} Projects', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save comparison plot
    output_file = f"{output_folder}/{difficulty_label.lower().replace(' ', '_')}_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Comparison plot saved: {output_file}")
    
    # Save comparison data
    comp_csv = f"{output_folder}/{difficulty_label.lower().replace(' ', '_')}_comparison.csv"
    comp_df.to_csv(comp_csv, index=False, encoding='utf-8-sig')
    print(f"Comparison data saved: {comp_csv}")

def create_special_labs_trend(year_dfs, output_folder, difficulty_label):
    """
    Create trend chart for special laboratories
    """
    print(f"\nCreating special labs trend chart for {difficulty_label} projects...")
    
    # Collect trend data
    trend_data = []
    
    for result_df, project_count, year, special_lab_info, label in year_dfs:
        if result_df is not None and special_lab_info is not None and label == difficulty_label:
            count_col = f'{difficulty_label.lower().replace(" ", "_")}_count_{year}'
            rank_col = f'{difficulty_label.lower().replace(" ", "_")}_rank_{year}'
            rate_col = f'{difficulty_label.lower().replace(" ", "_")}_rate_{year}'
            
            trend_data.append({
                'Year': year,
                'Labcode': special_lab_info['labcode'],
                'Detection': special_lab_info[count_col],
                'Total Projects': project_count,
                'Detection Rate': special_lab_info[rate_col],
                'Rank': special_lab_info[rank_col]
            })
    
    if len(trend_data) < 2:
        print(f"Not enough special lab data for {difficulty_label} trend chart")
        return
    
    trend_df = pd.DataFrame(trend_data)
    
    # Create trend chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Chart 1: Detection count trend
    years = trend_df['Year']
    labcodes = trend_df['Labcode']
    detections = trend_df['Detection']
    detection_rates = trend_df['Detection Rate']
    
    colors = ['red', 'green', 'blue', 'orange']
    
    for i, (year, labcode, detection, detection_rate, color) in enumerate(zip(years, labcodes, detections, detection_rates, colors)):
        ax1.bar(i, detection, color=color, alpha=0.7, edgecolor='black')
        ax1.text(i, detection + 0.1, f'{labcode}', 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
        # Add detection rate as text
        ax1.text(i, detection/2, f'{detection_rate:.1f}%', 
                ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel(f'{difficulty_label} Projects Detected', fontsize=12, fontweight='bold')
    ax1.set_title(f'Special Labs: {difficulty_label} Project Detection Trend', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(years)))
    ax1.set_xticklabels(years)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, detection in enumerate(detections):
        ax1.text(i, detection/2, f'{int(detection)}', 
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    
    # Chart 2: Ranking trend
    ranks = trend_df['Rank']
    
    ax2.plot(range(len(years)), ranks, marker='o', markersize=10, 
             linewidth=2, color='purple', alpha=0.7)
    
    for i, (year, labcode, rank, detection_rate) in enumerate(zip(years, labcodes, ranks, detection_rates)):
        ax2.text(i, rank + 0.5, f'{labcode}: Rank {int(rank)} ({detection_rate:.1f}%)', 
                ha='center', va='bottom', fontsize=9)
    
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Rank', fontsize=12, fontweight='bold')
    ax2.set_title(f'Special Labs: Ranking Trend on {difficulty_label} Projects', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(years)))
    ax2.set_xticklabels(years)
    ax2.invert_yaxis()  # Lower rank is better
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save trend chart
    output_file = f"{output_folder}/special_labs_{difficulty_label.lower().replace(' ', '_')}_trend.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Trend chart saved: {output_file}")
    
    # Save trend data
    trend_csv = f"{output_folder}/special_labs_{difficulty_label.lower().replace(' ', '_')}_trend.csv"
    trend_df.to_csv(trend_csv, index=False, encoding='utf-8-sig')
    print(f"Trend data saved: {trend_csv}")

def main():
    """
    Main function: Analyze projects by difficulty for 2021-2024
    """
    print("="*80)
    print("PROJECT DIFFICULTY ANALYSIS (2021-2024)")
    print("="*80)
    print("Difficulty Levels:")
    print("  1. High Difficulty: ≥0.9")
    print("  2. Medium Difficulty: >0.8 and <0.9")
    print("\nSpecial Laboratories by Year:")
    print("  2021: Lab 211")
    print("  2022: Lab 8") 
    print("  2023: Lab 43")
    print("  2024: Lab 5")
    print("="*80)
    
    # Difficulty configurations
    difficulty_configs = [
        {"min": 0.9, "max": None, "label": "High Difficulty"},
        {"min": 0.8, "max": 0.9, "label": "Medium Difficulty"}
    ]
    
    # Years to analyze
    years = [2021, 2022, 2023, 2024]
    
    for config in difficulty_configs:
        difficulty_min = config["min"]
        difficulty_max = config["max"]
        difficulty_label = config["label"]
        
        print(f"\n{'='*60}")
        print(f"ANALYZING {difficulty_label.upper()} PROJECTS")
        print(f"Difficulty Range: {difficulty_min}{f' to {difficulty_max}' if difficulty_max else '+'}")
        print(f"{'='*60}")
        
        # Create output folder
        output_folder = f"{difficulty_label.lower().replace(' ', '_')}_analysis_results"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Analyze each year
        year_dfs = []
        
        for year in years:
            print(f"\nAnalyzing {year}...")
            
            result_df, project_count, year_val, special_lab_info, label = analyze_year_projects_by_difficulty(
                year, difficulty_min, difficulty_max, difficulty_label)
            year_dfs.append((result_df, project_count, year_val, special_lab_info, label))
            
            if result_df is not None:
                count_col = f'{difficulty_label.lower().replace(" ", "_")}_count_{year_val}'
                rank_col = f'{difficulty_label.lower().replace(" ", "_")}_rank_{year_val}'
                rate_col = f'{difficulty_label.lower().replace(" ", "_")}_rate_{year_val}'
                
                print(f"\n{year_val} {difficulty_label} Summary:")
                print(f"  {difficulty_label} Projects: {project_count}")
                print(f"  Labs Detecting: {len(result_df)}")
                print(f"  Avg Detection per Lab: {result_df[count_col].mean():.2f}")
                print(f"  Max Detection: {result_df[count_col].max()}")
                print(f"  Min Detection: {result_df[count_col].min()}")
                
                if special_lab_info is not None:
                    print(f"\n  Special Lab Performance:")
                    print(f"    Lab Code: {special_lab_info['labcode']}")
                    print(f"    {difficulty_label} Projects Detected: {special_lab_info[count_col]}/{project_count}")
                    print(f"    Detection Rate: {special_lab_info[rate_col]:.1f}%")
                    print(f"    Rank: {special_lab_info[rank_col]}")
                    
                    # Calculate rank percentile
                    percentile = (special_lab_info[rank_col] / len(result_df)) * 100
                    print(f"    Rank Percentile: {percentile:.1f}%")
        
        # Create individual charts for each year
        create_year_specific_charts(year_dfs, output_folder, difficulty_label)
        
        # Create year comparison plot
        create_comparison_plot(year_dfs, output_folder, difficulty_label)
        
        # Create special labs trend chart
        create_special_labs_trend(year_dfs, output_folder, difficulty_label)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE!")
    print("Results saved to:")
    print("  - high_difficulty_analysis_results/")
    print("  - medium_difficulty_analysis_results/")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()