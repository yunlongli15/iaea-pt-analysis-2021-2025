import pandas as pd
import os
import glob

def analyze_lab_performance(lab_code='5'):
    """
    Analyze the performance of a specific laboratory in 2024
    Find: 
    1. Projects the lab did NOT participate in
    2. Projects the lab participated in but did NOT get 'A'
    """
    
    print("="*60)
    print(f"Laboratory Performance Analysis for Lab {lab_code} (2024)")
    print("="*60)
    
    # Folder path for 2024 data
    folder_path = "merged_labcode_tables_2024"
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    # Find all Excel files
    excel_files = glob.glob(f"{folder_path}/*.xlsx") + glob.glob(f"{folder_path}/*.xls")
    csv_files = glob.glob(f"{folder_path}/*.csv")
    all_files = excel_files + csv_files
    
    if not all_files:
        print("No data files found for 2024.")
        return
    
    print(f"Found {len(all_files)} analysis project files for 2024")
    
    # Results storage
    not_participated_projects = []  # Projects lab did NOT participate in
    failed_projects = []           # Projects lab participated in but did NOT get 'A'
    passed_projects = []           # Projects lab participated in and got 'A'
    
    # Statistics
    total_projects = len(all_files)
    participated_count = 0
    passed_count = 0
    failed_count = 0
    
    # Process each project file
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
            
            # Get project name from filename
            file_name = os.path.basename(file_path)
            project_name = extract_project_name(file_name)
            
            # Find labcode column
            labcode_col = find_labcode_column(df)
            if labcode_col is None:
                print(f"Warning: Could not find labcode column in {file_name}")
                continue
            
            # Find score column
            score_col = find_score_column(df)
            if score_col is None:
                print(f"Warning: Could not find score column in {file_name}")
                continue
            
            # Check if lab participated in this project
            lab_row = df[df[labcode_col].astype(str).str.strip().str.lower() == lab_code.lower()]
            
            if lab_row.empty:
                # Lab did NOT participate in this project
                not_participated_projects.append({
                    'Project': project_name,
                    'File': file_name,
                    'Reason': 'Not participated'
                })
            else:
                # Lab participated in this project
                participated_count += 1
                
                # Get the lab's score
                lab_score = str(lab_row.iloc[0][score_col]).strip().upper()
                
                if lab_score == 'A':
                    # Lab passed this project
                    passed_count += 1
                    passed_projects.append({
                        'Project': project_name,
                        'File': file_name,
                        'Score': lab_score,
                        'Participants': len(df)
                    })
                else:
                    # Lab did NOT get 'A' in this project
                    failed_count += 1
                    failed_projects.append({
                        'Project': project_name,
                        'File': file_name,
                        'Score': lab_score,
                        'Participants': len(df),
                        'A_Count': (df[score_col].astype(str).str.strip().str.upper() == 'A').sum(),
                        'A_Rate': ((df[score_col].astype(str).str.strip().str.upper() == 'A').sum() / len(df) * 100) if len(df) > 0 else 0
                    })
                    
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")
    
    # Print summary
    print(f"\nSummary for Lab {lab_code}:")
    print(f"Total Projects in 2024: {total_projects}")
    print(f"Projects Participated: {participated_count} ({participated_count/total_projects*100:.1f}%)")
    print(f"Projects Passed (A): {passed_count} ({passed_count/participated_count*100:.1f}% of participated)")
    print(f"Projects Failed (not A): {failed_count} ({failed_count/participated_count*100:.1f}% of participated)")
    print(f"Projects Not Participated: {len(not_participated_projects)} ({len(not_participated_projects)/total_projects*100:.1f}%)")
    
    # Create detailed reports
    create_detailed_reports(lab_code, not_participated_projects, failed_projects, passed_projects, total_projects)
    
    # Create summary chart
    create_summary_chart(lab_code, total_projects, participated_count, passed_count, failed_count)

def extract_project_name(file_name):
    """Extract project name from filename"""
    parts = file_name.split('_')
    if len(parts) >= 3:
        project_name_parts = parts[-3:]
    else:
        project_name_parts = parts
    
    project_name = ' '.join(project_name_parts).replace('.xlsx', '').replace('.xls', '').replace('.csv', '')
    return project_name

def find_labcode_column(df):
    """Find labcode column in dataframe"""
    for col_name in df.columns:
        if 'labcode' in str(col_name).lower():
            return col_name
    
    # If not found, try first column
    if len(df.columns) > 0:
        return df.columns[0]
    
    return None

def find_score_column(df):
    """Find score column in dataframe"""
    for col_name in df.columns:
        if 'final score' in str(col_name).lower() or 'z-score evaluation' in str(col_name).lower():
            return col_name
    
    return None

def create_detailed_reports(lab_code, not_participated_projects, failed_projects, passed_projects, total_projects):
    """Create detailed CSV reports"""
    
    # Create output folder
    output_folder = f"lab_{lab_code}_analysis_2024"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 1. Report: Projects NOT participated in
    if not_participated_projects:
        df_not_participated = pd.DataFrame(not_participated_projects)
        df_not_participated = df_not_participated.sort_values('Project')
        
        output_file = f"{output_folder}/lab_{lab_code}_not_participated_projects.csv"
        df_not_participated.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nProjects NOT participated in: {len(not_participated_projects)}")
        print(f"  Saved to: {output_file}")
        
        # Print top 10
        print(f"  Top 10 projects not participated in:")
        for i, row in df_not_participated.head(10).iterrows():
            print(f"    {i+1}. {row['Project']}")
    
    # 2. Report: Projects participated but NOT passed (not A)
    if failed_projects:
        df_failed = pd.DataFrame(failed_projects)
        df_failed = df_failed.sort_values('A_Rate', ascending=False)
        
        output_file = f"{output_folder}/lab_{lab_code}_failed_projects.csv"
        df_failed.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nProjects participated but NOT passed (not A): {len(failed_projects)}")
        print(f"  Saved to: {output_file}")
        
        # Print details
        print(f"  Details of failed projects:")
        for i, row in df_failed.head(10).iterrows():
            print(f"    {i+1}. {row['Project']}: Score={row['Score']}, A-rate={row['A_Rate']:.1f}%")
    
    # 3. Report: Projects passed (A)
    if passed_projects:
        df_passed = pd.DataFrame(passed_projects)
        df_passed = df_passed.sort_values('Project')
        
        output_file = f"{output_folder}/lab_{lab_code}_passed_projects.csv"
        df_passed.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nProjects passed (A): {len(passed_projects)}")
        print(f"  Saved to: {output_file}")
    
    # 4. Summary report
    summary_data = {
        'Metric': [
            'Total Projects in 2024',
            'Projects Participated',
            'Projects Passed (A)',
            'Projects Failed (not A)',
            'Projects Not Participated',
            'Participation Rate',
            'Success Rate (of participated)',
            'Success Rate (of total)'
        ],
        'Count': [
            total_projects,
            len(passed_projects) + len(failed_projects),
            len(passed_projects),
            len(failed_projects),
            len(not_participated_projects),
            f"{(len(passed_projects) + len(failed_projects)) / total_projects * 100:.1f}%",
            f"{len(passed_projects) / (len(passed_projects) + len(failed_projects)) * 100:.1f}%" if (len(passed_projects) + len(failed_projects)) > 0 else "0%",
            f"{len(passed_projects) / total_projects * 100:.1f}%"
        ],
        'Percentage': [
            '100%',
            f"{(len(passed_projects) + len(failed_projects)) / total_projects * 100:.1f}%",
            f"{len(passed_projects) / total_projects * 100:.1f}%",
            f"{len(failed_projects) / total_projects * 100:.1f}%",
            f"{len(not_participated_projects) / total_projects * 100:.1f}%",
            '-',
            '-',
            '-'
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    output_file = f"{output_folder}/lab_{lab_code}_summary.csv"
    df_summary.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nSummary report saved to: {output_file}")
    
    # 5. Combined detailed report
    combined_data = []
    
    # Add not participated projects
    for project in not_participated_projects:
        combined_data.append({
            'Project': project['Project'],
            'Status': 'Not Participated',
            'Score': 'N/A',
            'A_Rate': 'N/A',
            'Participants': 'N/A',
            'File': project['File']
        })
    
    # Add failed projects
    for project in failed_projects:
        combined_data.append({
            'Project': project['Project'],
            'Status': 'Failed',
            'Score': project['Score'],
            'A_Rate': f"{project['A_Rate']:.1f}%",
            'Participants': project['Participants'],
            'File': project['File']
        })
    
    # Add passed projects
    for project in passed_projects:
        combined_data.append({
            'Project': project['Project'],
            'Status': 'Passed',
            'Score': 'A',
            'A_Rate': 'N/A',
            'Participants': project['Participants'],
            'File': project['File']
        })
    
    df_combined = pd.DataFrame(combined_data)
    df_combined = df_combined.sort_values(['Status', 'Project'])
    
    output_file = f"{output_folder}/lab_{lab_code}_all_projects.csv"
    df_combined.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Combined detailed report saved to: {output_file}")

def create_summary_chart(lab_code, total_projects, participated_count, passed_count, failed_count):
    """Create a summary visualization chart"""
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Data for pie chart
    labels = ['Passed (A)', 'Failed (not A)', 'Not Participated']
    sizes = [passed_count, failed_count, total_projects - participated_count]
    colors = ['#4CAF50', '#F44336', '#9E9E9E']
    explode = (0.1, 0, 0)  # explode the 'Passed' slice
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.set_title(f'Lab {lab_code} Performance Distribution (2024)', fontsize=14, fontweight='bold')
    
    # Bar chart
    categories = ['Total Projects', 'Participated', 'Passed (A)']
    values = [total_projects, participated_count, passed_count]
    percentages = ['100%', 
                  f'{participated_count/total_projects*100:.1f}%',
                  f'{passed_count/total_projects*100:.1f}%']
    
    bars = ax2.bar(categories, values, color=['#2196F3', '#FF9800', '#4CAF50'], alpha=0.8)
    ax2.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Projects', fontsize=12, fontweight='bold')
    ax2.set_title(f'Lab {lab_code} Performance Metrics (2024)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, value, percentage in zip(bars, values, percentages):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{value}\n({percentage})', ha='center', va='bottom', fontsize=10)
    
    # Add success rate annotation
    success_rate_participated = (passed_count / participated_count * 100) if participated_count > 0 else 0
    success_rate_total = (passed_count / total_projects * 100) if total_projects > 0 else 0
    
    annotation_text = (f"Success Rate (of participated): {success_rate_participated:.1f}%\n"
                      f"Success Rate (of total): {success_rate_total:.1f}%\n"
                      f"Participation Rate: {participated_count/total_projects*100:.1f}%")
    
    ax2.text(0.02, 0.98, annotation_text, transform=ax2.transAxes,
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save chart
    output_folder = f"lab_{lab_code}_analysis_2024"
    output_file = f"{output_folder}/lab_{lab_code}_performance_summary.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"\nPerformance summary chart saved to: {output_file}")

def main():
    """
    Main function to analyze lab performance
    """
    print("Laboratory Performance Analysis Program")
    print("This program analyzes the performance of a specific laboratory in 2024.")
    print("It identifies:")
    print("  1. Projects the lab did NOT participate in")
    print("  2. Projects the lab participated in but did NOT get 'A' (accepted)")
    print()
    
    # You can change this to analyze a different lab
    lab_code = '5'  # Default: Lab 5 (special lab for 2024)
    
    # Uncomment below to analyze a different lab
    # lab_code = input("Enter laboratory code to analyze (default: 5): ").strip() or '5'
    
    analyze_lab_performance(lab_code)
    
    print("\n" + "="*60)
    print("Analysis Complete!")
    print("="*60)

if __name__ == "__main__":
    main()