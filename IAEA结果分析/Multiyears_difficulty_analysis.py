import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Define years to analyze
years = [2021, 2022, 2023, 2024]

# Dictionary to store total participants for each year
# You may need to adjust these numbers based on actual data
yearly_total_participants = {
    2021: 326,  # Adjust based on actual 2021 data
    2022: 287,  # Adjust based on actual 2022 data
    2023: 316,  # Adjust based on actual 2023 data
    2024: 476   # Based on your information
}

# Base folder structure (assuming similar structure for each year)
# Example: merged_labcode_tables_2021, merged_labcode_tables_2022, etc.
base_folder_name = "merged_labcode_tables"

# 修改读取和处理文件的部分代码

def analyze_year(year):
    """Analyze data for a specific year"""
    print(f"\n{'='*60}")
    print(f"ANALYZING YEAR: {year}")
    print(f"{'='*60}")
    
    # Construct folder path for the year
    folder_path = f"{base_folder_name}_{year}"
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Warning: Folder '{folder_path}' does not exist. Skipping year {year}.")
        return None
    
    # Store results for this year
    year_results = []
    
    # Process all files in the folder
    files_processed = 0
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            file_path = os.path.join(folder_path, file_name)
            
            try:
                # Read Excel file
                df = pd.read_excel(file_path)
                
                # 确定使用哪个评分列
                score_column = None
                if 'Final Score' in df.columns:
                    score_column = 'Final Score'
                elif 'Z-Score Evaluation' in df.columns:
                    score_column = 'Z-Score Evaluation'
                else:
                    print(f"Warning: File {file_name} doesn't have 'Final Score' or 'Z-Score Evaluation' column. Skipping.")
                    continue  # 跳过这个文件
                
                # Count number of labs for this project (excluding header)
                total_participants = len(df)
                
                # Count A's (satisfactory results)
                # 使用确定的评分列
                a_count = df[score_column].str.upper().eq('A').sum()
                
                # Extract project name from filename
                parts = file_name.split('_')
                if len(parts) >= 3:
                    project_name_parts = parts[-3:]
                else:
                    project_name_parts = parts
                
                project_name = ' '.join(project_name_parts).replace('.xlsx', '').replace('.xls', '')
                
                # Get total participants for this year
                total_year_participants = yearly_total_participants.get(year, 0)
                
                # Calculate difficulty coefficient (based on year total participants)
                if total_year_participants > 0:
                    difficulty_coefficient = 1 - (a_count / total_year_participants)
                else:
                    difficulty_coefficient = 0
                
                # Calculate pass rate (based on actual participants in this project)
                pass_rate = a_count / total_participants if total_participants > 0 else 0
                
                year_results.append({
                    'Project Name': project_name,
                    'File Name': file_name,
                    'Year': year,
                    'Score Column Used': score_column,  # 记录使用了哪个评分列
                    'Total Participants': total_participants,
                    'A Count': a_count,
                    'Difficulty Coefficient': difficulty_coefficient,
                    'Pass Rate': pass_rate
                })
                
                files_processed += 1
                print(f"Processed: {file_name}, Used column: {score_column}, "
                      f"A's: {a_count}/{total_participants}")
                    
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
    
    print(f"Processed {files_processed} files for year {year}")
    
    if year_results:
        return pd.DataFrame(year_results)
    else:
        return None
def create_plot_for_year(year_df, year):
    """Create visualization for a specific year's data"""
    if year_df is None or len(year_df) == 0:
        print(f"No data to plot for year {year}")
        return
    
    # Sort by Difficulty Coefficient
    year_df_sorted = year_df.sort_values('Difficulty Coefficient', ascending=False)
    
    # Set up the plot
    fig, ax1 = plt.subplots(figsize=(16, 10))
    
    # Bar width and positions
    x_positions = np.arange(len(year_df_sorted))
    bar_width = 0.35
    
    # Plot Difficulty Coefficient (left y-axis)
    bars1 = ax1.bar(x_positions - bar_width/2, 
                   year_df_sorted['Difficulty Coefficient'], 
                   width=bar_width, 
                   color='skyblue', 
                   alpha=0.8, 
                   label='Difficulty Coefficient')
    
    ax1.set_xlabel('Analysis Project', fontsize=12, fontweight='bold')
    ax1.set_ylabel(f'Difficulty Coefficient\n(1 - A Count / {yearly_total_participants.get(year, "N/A")})', 
                   color='darkblue', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='darkblue')
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(year_df_sorted['Project Name'], rotation=45, ha='right', fontsize=10)
    
    # Set y-axis limits for Difficulty Coefficient
    max_difficulty = year_df_sorted['Difficulty Coefficient'].max()
    ax1.set_ylim([0, max(max_difficulty * 1.1, 0.1)])  # Ensure at least 0.1 for visibility
    
    # Create second y-axis for Pass Rate
    ax2 = ax1.twinx()
    
    # Plot Pass Rate as line with markers
    line = ax2.plot(x_positions + bar_width/2, 
                   year_df_sorted['Pass Rate'], 
                   color='crimson', 
                   marker='o', 
                   markersize=6, 
                   linewidth=2, 
                   label='Pass Rate')
    
    ax2.set_ylabel('Pass Rate\n(A Count / Participants)', 
                   color='crimson', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='crimson')
    ax2.set_ylim([0, 1.1])  # Pass rate between 0 and 1
    
    # Add grid
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add title
    plt.title(f'{year} Proficiency Testing: Difficulty Coefficient vs Pass Rate by Analysis Project', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    lines_labels1 = ax1.get_legend_handles_labels()
    lines_labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_labels1[0] + lines_labels2[0], 
              lines_labels1[1] + lines_labels2[1], 
              loc='upper left')
    
    # Add value labels on bars (only if not too crowded)
    if len(year_df_sorted) <= 50:  # Only add labels if reasonable number of projects
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.3f}', ha='center', va='bottom', 
                    fontsize=8, color='darkblue')
    
    # Add value labels for Pass Rate points
    if len(year_df_sorted) <= 50:  # Only add labels if reasonable number of projects
        for i, (x, rate) in enumerate(zip(x_positions + bar_width/2, year_df_sorted['Pass Rate'])):
            ax2.text(x, rate + 0.02, f'{rate:.3f}', 
                    ha='center', va='bottom', 
                    fontsize=8, color='crimson')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    output_filename = f'{year}_Project_Difficulty_Analysis.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {output_filename}")
    
    # Show the plot
    plt.show()
    
    return year_df_sorted

def print_year_statistics(year_df, year):
    """Print statistics for a specific year"""
    if year_df is None or len(year_df) == 0:
        print(f"No statistics available for year {year}")
        return
    
    print(f"\n{'='*60}")
    print(f"{year} ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Projects Analyzed: {len(year_df)}")
    print(f"Average Difficulty Coefficient: {year_df['Difficulty Coefficient'].mean():.4f}")
    print(f"Median Difficulty Coefficient: {year_df['Difficulty Coefficient'].median():.4f}")
    print(f"Average Pass Rate: {year_df['Pass Rate'].mean():.4f}")
    print(f"Median Pass Rate: {year_df['Pass Rate'].median():.4f}")
    
    # Save detailed results to CSV
    csv_filename = f'{year}_Project_Difficulty_Analysis_Results.csv'
    year_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"Detailed results saved to: {csv_filename}")

def create_comparison_plot(all_year_data):
    """Create a comparison plot across all years"""
    if not all_year_data:
        print("No data available for comparison plot")
        return
    
    # Prepare data for comparison
    comparison_data = []
    
    for year, year_df in all_year_data.items():
        if year_df is not None and len(year_df) > 0:
            avg_difficulty = year_df['Difficulty Coefficient'].mean()
            avg_pass_rate = year_df['Pass Rate'].mean()
            total_projects = len(year_df)
            
            comparison_data.append({
                'Year': year,
                'Avg Difficulty': avg_difficulty,
                'Avg Pass Rate': avg_pass_rate,
                'Total Projects': total_projects
            })
    
    if not comparison_data:
        return
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Average Difficulty Coefficient by Year
    years = comparison_df['Year']
    x_pos = np.arange(len(years))
    
    bars1 = ax1.bar(x_pos, comparison_df['Avg Difficulty'], 
                    color='skyblue', alpha=0.7, label='Average Difficulty')
    ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Average Difficulty Coefficient', color='darkblue', fontsize=12, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(years)
    ax1.tick_params(axis='y', labelcolor='darkblue')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_title('Average Difficulty Coefficient by Year', fontsize=14, fontweight='bold')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontsize=10)
    
    # Plot 2: Average Pass Rate by Year
    ax2.plot(x_pos, comparison_df['Avg Pass Rate'], 
             color='crimson', marker='o', markersize=10, linewidth=3, label='Average Pass Rate')
    ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Average Pass Rate', color='crimson', fontsize=12, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(years)
    ax2.tick_params(axis='y', labelcolor='crimson')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim([0, 1])
    ax2.set_title('Average Pass Rate by Year', fontsize=14, fontweight='bold')
    
    # Add value labels on points
    for i, (x, y) in enumerate(zip(x_pos, comparison_df['Avg Pass Rate'])):
        ax2.text(x, y + 0.02, f'{y:.3f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    #plt.savefig('Yearly_Comparison_Analysis.png', dpi=300, bbox_inches='tight')
    #print("Saved comparison plot: Yearly_Comparison_Analysis.png")
    plt.show()
    
    # Print comparison statistics
    print(f"\n{'='*60}")
    print("YEAR-OVER-YEAR COMPARISON")
    print(f"{'='*60}")
    print(comparison_df.to_string(index=False))

# Main execution
def main():
    all_year_data = {}
    
    # Analyze each year
    for year in years:
        year_df = analyze_year(year)
        if year_df is not None:
            all_year_data[year] = year_df
            create_plot_for_year(year_df, year)
            print_year_statistics(year_df, year)
    
    # Create comparison plot
    create_comparison_plot(all_year_data)
    
    # Create combined summary
    if all_year_data:
        print(f"\n{'='*60}")
        print("COMBINED SUMMARY (2021-2024)")
        print(f"{'='*60}")
        
        summary_rows = []
        for year, year_df in all_year_data.items():
            if year_df is not None and len(year_df) > 0:
                summary_rows.append({
                    'Year': year,
                    'Projects': len(year_df),
                    'Avg Difficulty': f"{year_df['Difficulty Coefficient'].mean():.4f}",
                    'Avg Pass Rate': f"{year_df['Pass Rate'].mean():.4f}",
                    'Total Participants (All Projects)': year_df['Total Participants'].sum(),
                    'Max Difficulty': f"{year_df['Difficulty Coefficient'].max():.4f}",
                    'Min Difficulty': f"{year_df['Difficulty Coefficient'].min():.4f}"
                })
        
        summary_df = pd.DataFrame(summary_rows)
        print(summary_df.to_string(index=False))
        
        # Save combined summary
        #summary_df.to_csv('Combined_Yearly_Summary_2021-2024.csv', index=False, encoding='utf-8-sig')
        #print("\nCombined summary saved to: Combined_Yearly_Summary_2021-2024.csv")

if __name__ == "__main__":
    main()