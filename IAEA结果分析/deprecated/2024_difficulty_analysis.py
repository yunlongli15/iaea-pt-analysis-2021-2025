import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set folder path
folder_path = "merged_labcode_tables_2024"
total_labs_2024 = 476  # Total participants in 2024

# Store results
results = []

# Process all files in the folder
for file_name in os.listdir(folder_path):
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        file_path = os.path.join(folder_path, file_name)
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check if "Final Score" column exists
            if 'Final Score' in df.columns:
                # Count number of labs for this project (excluding header)
                total_participants = len(df)
                
                # Count A's (satisfactory results)
                a_count = df['Final Score'].str.upper().eq('A').sum()
                
                # Extract project name from filename
                # Assuming format: 001_Labcode_2-516_Eu-152_Gamma_Water.xlsx
                parts = file_name.split('_')
                # Get the last few parts as project name (excluding extension)
                if len(parts) >= 3:
                    project_name_parts = parts[-3:]
                else:
                    project_name_parts = parts
                
                project_name = ' '.join(project_name_parts).replace('.xlsx', '').replace('.xls', '')
                
                # Calculate difficulty coefficient (based on 2024 total labs)
                difficulty_coefficient = 1 - (a_count / total_labs_2024)
                
                # Calculate pass rate (based on actual participants in this project)
                pass_rate = a_count / total_participants if total_participants > 0 else 0
                
                results.append({
                    'Project Name': project_name,
                    'File Name': file_name,
                    'Total Participants': total_participants,
                    'A Count': a_count,
                    'Difficulty Coefficient': difficulty_coefficient,
                    'Pass Rate': pass_rate
                })
                
                print(f"Processed: {file_name}, Project: {project_name}, "
                      f"Participants: {total_participants}, A's: {a_count}, "
                      f"Difficulty: {difficulty_coefficient:.4f}, Pass Rate: {pass_rate:.4f}")
            else:
                print(f"Warning: File {file_name} doesn't have 'Final Score' column")
                
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

# Convert to DataFrame and sort by Difficulty Coefficient
if results:
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Difficulty Coefficient', ascending=False)
    
    # Set up the plot
    fig, ax1 = plt.subplots(figsize=(16, 10))
    
    # Bar width and positions
    x_positions = np.arange(len(results_df))
    bar_width = 0.35
    
    # Plot Difficulty Coefficient (left y-axis)
    bars1 = ax1.bar(x_positions - bar_width/2, 
                   results_df['Difficulty Coefficient'], 
                   width=bar_width, 
                   color='skyblue', 
                   alpha=0.8, 
                   label='Difficulty Coefficient')
    
    ax1.set_xlabel('Analysis Project', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Difficulty Coefficient\n(1 - A Count / 476)', 
                   color='darkblue', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='darkblue')
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(results_df['Project Name'], rotation=45, ha='right', fontsize=10)
    
    # Set y-axis limits for Difficulty Coefficient
    ax1.set_ylim([0, max(results_df['Difficulty Coefficient']) * 1.1])
    
    # Create second y-axis for Pass Rate
    ax2 = ax1.twinx()
    
    # Plot Pass Rate as line with markers
    line = ax2.plot(x_positions + bar_width/2, 
                   results_df['Pass Rate'], 
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
    plt.title('2024 Proficiency Testing: Difficulty Coefficient vs Pass Rate by Analysis Project', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Add legend - combine both
    lines_labels1 = ax1.get_legend_handles_labels()
    lines_labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_labels1[0] + lines_labels2[0], 
              lines_labels1[1] + lines_labels2[1], 
              loc='upper left')
    
    # Add value labels on bars
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', 
                fontsize=8, color='darkblue')
    
    # Add value labels for Pass Rate points
    for i, (x, rate) in enumerate(zip(x_positions + bar_width/2, results_df['Pass Rate'])):
        ax2.text(x, rate + 0.02, f'{rate:.3f}', 
                ha='center', va='bottom', 
                fontsize=8, color='crimson')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    plt.savefig('2024_Project_Difficulty_Analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Display statistics
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Projects Analyzed: {len(results_df)}")
    print(f"Average Difficulty Coefficient: {results_df['Difficulty Coefficient'].mean():.4f}")
    print(f"Median Difficulty Coefficient: {results_df['Difficulty Coefficient'].median():.4f}")
    print(f"Average Pass Rate: {results_df['Pass Rate'].mean():.4f}")
    print(f"Median Pass Rate: {results_df['Pass Rate'].median():.4f}")
    
    print("\n" + "="*60)
    print("TOP 10 MOST DIFFICULT PROJECTS")
    print("="*60)
    print(results_df.head(10)[['Project Name', 'Total Participants', 
                               'A Count', 'Difficulty Coefficient', 'Pass Rate']].to_string(index=False))
    
    print("\n" + "="*60)
    print("TOP 10 EASIEST PROJECTS")
    print("="*60)
    print(results_df.tail(10)[['Project Name', 'Total Participants', 
                               'A Count', 'Difficulty Coefficient', 'Pass Rate']].sort_values('Difficulty Coefficient').to_string(index=False))
    
    # Save detailed results to CSV
    results_df.to_csv('2024_Project_Difficulty_Analysis_Results.csv', 
                     index=False, encoding='utf-8-sig')
    print(f"\nDetailed results saved to: 2024_Project_Difficulty_Analysis_Results.csv")
    
    # Create a summary statistics table
    summary_stats = pd.DataFrame({
        'Metric': ['Number of Projects', 'Total Participants (All Projects)', 
                   'Average Participants per Project', 'Average A Count',
                   'Average Difficulty Coefficient', 'Average Pass Rate',
                   'Max Difficulty Coefficient', 'Min Difficulty Coefficient',
                   'Max Pass Rate', 'Min Pass Rate'],
        'Value': [len(results_df),
                 results_df['Total Participants'].sum(),
                 results_df['Total Participants'].mean(),
                 results_df['A Count'].mean(),
                 results_df['Difficulty Coefficient'].mean(),
                 results_df['Pass Rate'].mean(),
                 results_df['Difficulty Coefficient'].max(),
                 results_df['Difficulty Coefficient'].min(),
                 results_df['Pass Rate'].max(),
                 results_df['Pass Rate'].min()]
    })
    
    print("\n" + "="*60)
    print("COMPREHENSIVE STATISTICS")
    print("="*60)
    print(summary_stats.to_string(index=False))
    
else:
    print("No valid data found in the folder.")