import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

def extract_project_name(file_path):
    """
    从文件名中提取项目名称
    """
    filename = os.path.basename(file_path)
    # 常见项目名称匹配
    project_keywords = {
        'H-3': ['h-3', 'h3', 'tritium'],
        'Sr-90': ['sr-90', 'sr90', 'strontium'],
        'Cs-137': ['cs-137', 'cs137', 'cesium'],
        'Water': ['water', 'aqua', 'liquid'],
        'Soil': ['soil', 'sediment', 'earth'],
        'Beta': ['beta', 'β'],
        'Gamma': ['gamma', 'γ']
    }
    
    filename_lower = filename.lower()
    
    # 尝试识别项目类型
    if any(keyword in filename_lower for keyword in project_keywords['H-3']):
        if any(keyword in filename_lower for keyword in project_keywords['Beta']) and \
           any(keyword in filename_lower for keyword in project_keywords['Water']):
            return 'H-3 Beta Water'
    
    if any(keyword in filename_lower for keyword in project_keywords['Sr-90']):
        if any(keyword in filename_lower for keyword in project_keywords['Beta']) and \
           any(keyword in filename_lower for keyword in project_keywords['Water']):
            return 'Sr-90 Beta Water'
    
    if any(keyword in filename_lower for keyword in project_keywords['Cs-137']):
        if any(keyword in filename_lower for keyword in project_keywords['Gamma']) and \
           any(keyword in filename_lower for keyword in project_keywords['Soil']):
            return 'Cs-137 Gamma Soil'
    
    return None

def analyze_project_2024(project_name):
    """
    分析特定项目的2024年实验室偏差
    project_name: 项目名称，如 'H-3 Beta Water', 'Sr-90 Beta Water', 'Cs-137 Gamma Soil'
    """
    
    print(f"\n{'='*70}")
    print(f"Analyzing project: {project_name} (2024 only)")
    print(f"{'='*70}")
    
    # 创建项目特定的输出文件夹
    project_folder = f"project_analysis_2024_{project_name.replace(' ', '_').replace('-', '_')}"
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    
    # 只分析2024年的数据
    year = 2024
    folder_path = f"merged_labcode_tables_{year}"
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return None, None
    
    # 查找该年份的所有文件
    excel_files = glob.glob(f"{folder_path}/*.xlsx") + glob.glob(f"{folder_path}/*.xls")
    csv_files = glob.glob(f"{folder_path}/*.csv")
    all_files = excel_files + csv_files
    
    if not all_files:
        print(f"{year}: No data files found")
        return None, None
    
    # 筛选属于该项目的文件
    project_files = []
    for file_path in all_files:
        detected_project = extract_project_name(file_path)
        if detected_project == project_name:
            project_files.append(file_path)
    
    if not project_files:
        print(f"{year}: No files found for project {project_name}")
        return None, None
    
    print(f"{year}: Found {len(project_files)} files for project {project_name}")
    
    # 收集所有实验室在该项目上的数据
    lab_bias_data = defaultdict(list)  # lab -> list of bias absolute values
    lab_file_count = defaultdict(int)  # lab -> count of files participated
    
    # 处理每个文件
    for file_path in project_files:
        try:
            # 读取文件
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                # 尝试不同编码
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except:
                        df = pd.read_csv(file_path, encoding='latin1')
            
            # 查找labcode列和relative bias列
            labcode_col = None
            bias_col = None
            
            for col_name in df.columns:
                col_lower = str(col_name).lower()
                if 'labcode' in col_lower:
                    labcode_col = col_name
                elif 'relative bias' in col_lower:
                    bias_col = col_name
                elif 'bias' in col_lower and 'relative' not in col_lower:
                    # 检查是否可能是相对偏差的不同名称
                    bias_col = col_name
            
            # 如果未找到labcode列，使用第一列
            if labcode_col is None and len(df.columns) > 0:
                labcode_col = df.columns[0]
            
            if labcode_col is not None and bias_col is not None:
                # 处理该文件中的每个实验室
                for idx, row in df.iterrows():
                    lab = str(row[labcode_col]).strip()
                    if not lab or pd.isna(lab):
                        continue
                    
                    bias_value = row[bias_col]
                    if not pd.isna(bias_value):
                        try:
                            # 转换为浮点数并取绝对值
                            bias_abs = abs(float(bias_value))
                            lab_bias_data[lab].append(bias_abs)
                            lab_file_count[lab] += 1
                        except (ValueError, TypeError):
                            continue
                        
        except Exception as e:
            print(f"Error processing file {os.path.basename(file_path)}: {e}")
    
    # 计算每个实验室的统计指标
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
                'n_measurements': len(bias_values),
                'n_files': lab_file_count[lab]
            }
    
    if not lab_bias_stats:
        print(f"No data found for project {project_name} in 2024")
        return None, None
    
    # 转换为DataFrame并排序
    rows = []
    for lab, stats in lab_bias_stats.items():
        rows.append({
            'labcode': lab,
            'bias_mean_2024': stats['bias_mean'],
            'bias_variance_2024': stats['bias_variance'],
            'bias_std_2024': stats['bias_std'],
            'n_measurements': stats['n_measurements'],
            'n_files': stats['n_files']
        })
    
    df = pd.DataFrame(rows)
    
    # 按照偏差平均值排序（越小越好）
    df = df.sort_values('bias_mean_2024', ascending=True).reset_index(drop=True)
    
    # 计算排名
    current_rank = 1
    ranks = []
    prev_mean = None
    
    for mean in df['bias_mean_2024']:
        if prev_mean is None or mean != prev_mean:
            current_rank = len(ranks) + 1
        ranks.append(current_rank)
        prev_mean = mean
    
    df['rank_2024'] = ranks
    
    # 标记特殊实验室（2024年的特殊实验室是5）
    special_lab_2024 = '5'
    
    df['is_special'] = False
    df['special_note'] = ''
    
    special_mask = df['labcode'].astype(str).str.strip().str.lower() == special_lab_2024.lower()
    if special_mask.any():
        df.loc[special_mask, 'is_special'] = True
        df.loc[special_mask, 'special_note'] = '2024 Special Lab'
        print(f"  Found special laboratory for 2024: {df.loc[special_mask, 'labcode'].iloc[0]}")
    
    return df, project_files

def create_project_analysis_chart_2024(project_name, df, project_files):
    """
    创建项目分析图表（2024年）
    """
    if df is None or len(df) == 0:
        print(f"No data to create chart for project {project_name}")
        return
    
    # 创建项目文件夹
    project_folder = f"project_analysis_2024_{project_name.replace(' ', '_').replace('-', '_')}"
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    
    print(f"\nCreating chart for project: {project_name} (2024)")
    
    # 过滤偏差在0-50范围内的实验室
    df_filtered = df[df['bias_mean_2024'] <= 50].copy()
    
    if len(df_filtered) == 0:
        print(f"  No labs with bias within 0-50 range for {project_name}")
        return
    
    # 按照偏差平均值排序
    df_filtered = df_filtered.sort_values('bias_mean_2024', ascending=True).reset_index(drop=True)
    df_filtered['x'] = range(len(df_filtered))
    
    print(f"  Displaying {len(df_filtered)}/{len(df)} labs with bias ≤ 50")
    
    # 分离特殊实验室和普通实验室
    special_df = df_filtered[df_filtered['is_special']].copy()
    regular_df = df_filtered[~df_filtered['is_special']].copy()
    
    # 创建散点图
    plt.figure(figsize=(16, 8))
    
    # 绘制普通实验室
    if len(regular_df) > 0:
        plt.errorbar(regular_df['x'], regular_df['bias_mean_2024'], 
                    yerr=regular_df['bias_std_2024'],  # 使用标准差作为误差棒
                    fmt='o', 
                    markersize=6,
                    color='skyblue',
                    alpha=0.7,
                    ecolor='lightgray',
                    elinewidth=0.5,
                    capsize=2,
                    zorder=5,
                    label='Regular Labs')
    
    # 绘制特殊实验室
    if len(special_df) > 0:
        for _, row in special_df.iterrows():
            plt.errorbar(row['x'], row['bias_mean_2024'], 
                        yerr=row['bias_std_2024'],
                        fmt='o', 
                        markersize=12,
                        color='orange',
                        alpha=0.9,
                        ecolor='gray',
                        elinewidth=1,
                        capsize=3,
                        zorder=10,
                        label='2024 Special Lab (5)')
    
    # 设置X轴标签
    plt.xticks(df_filtered['x'], df_filtered['labcode'], rotation=90, ha='right', fontsize=6)
    
    # 设置轴标签
    plt.xlabel('Laboratory Code (Sorted by Average Bias)', fontsize=12, fontweight='bold')
    plt.ylabel(f'Average Bias Deviation (2024)', fontsize=12, fontweight='bold')
    
    # 添加网格
    plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
    
    # 调整轴范围
    plt.xlim(-1, len(df_filtered))
    plt.ylim(0, 50)  # 固定Y轴范围0-50
    
    # 添加特殊实验室标签
    for _, row in special_df.iterrows():
        text_offset = 15 if row['bias_mean_2024'] < 40 else -15
        
        plt.annotate(f"{row['labcode']} (2024 Special)",
                    xy=(row['x'], row['bias_mean_2024']),
                    xytext=(0, text_offset),
                    textcoords='offset points',
                    ha='center',
                    fontsize=9,
                    fontweight='bold',
                    color='black',
                    bbox=dict(boxstyle='round,pad=0.3', 
                             facecolor='yellow', 
                             alpha=0.8, 
                             edgecolor='black'))
    
    # 计算统计信息
    avg_bias = df_filtered['bias_mean_2024'].mean()
    min_bias = df_filtered['bias_mean_2024'].min()
    max_bias = df_filtered['bias_mean_2024'].max()
    avg_std = df_filtered['bias_std_2024'].mean()
    
    # 计算所有实验室的统计信息（包括>50的）
    avg_bias_all = df['bias_mean_2024'].mean()
    max_bias_all = df['bias_mean_2024'].max()
    outliers_count = len(df) - len(df_filtered)
    
    # 获取特殊实验室信息
    special_info = ""
    if not special_df.empty:
        for _, row in special_df.iterrows():
            special_info += (f"{row['labcode']}: Rank {row['rank_2024']}, "
                           f"Bias: {row['bias_mean_2024']:.3f}±{row['bias_std_2024']:.3f}, "
                           f"Measurements: {row['n_measurements']}; ")
    
    stats_text = (f"Total Labs: {len(df)} | Displayed: {len(df_filtered)} | Outliers (>50): {outliers_count} | "
                 f"Avg Bias (shown): {avg_bias:.3f} | Min: {min_bias:.3f} | Max (shown): {max_bias:.3f} | "
                 f"Avg Bias (all): {avg_bias_all:.3f} | Max (all): {max_bias_all:.3f}")
    
    title_text = f'{project_name} - Laboratory Bias Analysis (2024)\n{stats_text}\nTotal Files: {len(project_files)}'
    
    if special_info:
        title_text += f"\nSpecial Lab: {special_info}"
    
    plt.title(title_text, fontsize=14, fontweight='bold', pad=25)
    
    # 添加水平参考线
    plt.axhline(y=50, color='red', linestyle='--', alpha=0.3, linewidth=1, label='Upper Limit (50)')
    
    # 添加图例
    plt.legend(loc='upper right')
    
    # 调整布局
    plt.tight_layout(rect=[0.03, 0.05, 0.97, 0.95])
    
    # 保存图表
    output_file = f"{project_folder}/{project_name.replace(' ', '_').replace('-', '_')}_bias_analysis_2024.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Chart saved: {output_file}")
    
    # 保存详细数据
    csv_file = f"{project_folder}/{project_name.replace(' ', '_').replace('-', '_')}_bias_data_2024.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"Data saved: {csv_file}")
    
    # 保存筛选后的数据
    csv_filtered_file = f"{project_folder}/{project_name.replace(' ', '_').replace('-', '_')}_bias_data_2024_filtered.csv"
    df_filtered.to_csv(csv_filtered_file, index=False, encoding='utf-8-sig')
    print(f"Filtered data saved: {csv_filtered_file}")
    
    # 生成汇总报告
    create_project_summary_2024(project_name, df, project_files, project_folder)

def create_project_summary_2024(project_name, df, project_files, project_folder):
    """
    创建项目分析摘要报告（2024年）
    """
    summary_file = f"{project_folder}/{project_name.replace(' ', '_').replace('-', '_')}_summary_2024.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"{project_name} - Laboratory Bias Analysis Summary (2024)\n")
        f.write("="*80 + "\n\n")
        
        # 项目文件信息
        f.write("PROJECT FILES (2024):\n")
        f.write("-"*40 + "\n")
        f.write(f"Total files: {len(project_files)}\n")
        for i, file_path in enumerate(project_files, 1):
            f.write(f"{i}. {os.path.basename(file_path)}\n")
        f.write("\n")
        
        # 实验室统计
        f.write("LABORATORY STATISTICS (2024):\n")
        f.write("-"*40 + "\n")
        f.write(f"Total laboratories: {len(df)}\n")
        f.write(f"Laboratories with bias ≤ 50: {len(df[df['bias_mean_2024'] <= 50])}\n")
        f.write(f"Laboratories with bias > 50: {len(df[df['bias_mean_2024'] > 50])}\n\n")
        
        # 偏差统计
        f.write("BIAS STATISTICS (2024):\n")
        f.write("-"*40 + "\n")
        f.write(f"Average bias (all labs): {df['bias_mean_2024'].mean():.4f}\n")
        f.write(f"Minimum bias (best): {df['bias_mean_2024'].min():.4f}\n")
        f.write(f"Maximum bias (worst): {df['bias_mean_2024'].max():.4f}\n")
        f.write(f"Standard deviation of bias: {df['bias_mean_2024'].std():.4f}\n\n")
        
        # 参与情况统计
        f.write("PARTICIPATION STATISTICS (2024):\n")
        f.write("-"*40 + "\n")
        f.write(f"Average measurements per lab: {df['n_measurements'].mean():.1f}\n")
        f.write(f"Labs with 1 measurement: {len(df[df['n_measurements'] == 1])}\n")
        f.write(f"Labs with 2-5 measurements: {len(df[(df['n_measurements'] >= 2) & (df['n_measurements'] <= 5)])}\n")
        f.write(f"Labs with >5 measurements: {len(df[df['n_measurements'] > 5])}\n\n")
        
        # 特殊实验室信息
        special_df = df[df['is_special']]
        if not special_df.empty:
            f.write("SPECIAL LABORATORY (2024):\n")
            f.write("-"*40 + "\n")
            for _, row in special_df.iterrows():
                f.write(f"{row['labcode']}:\n")
                f.write(f"  Rank: {row['rank_2024']}/{len(df)}\n")
                f.write(f"  Bias: {row['bias_mean_2024']:.4f} ± {row['bias_std_2024']:.4f}\n")
                f.write(f"  Measurements: {row['n_measurements']}\n")
                f.write(f"  Files participated: {row['n_files']}\n\n")
        
        # 前10名实验室
        f.write("TOP 10 LABORATORIES (LOWEST BIAS - 2024):\n")
        f.write("-"*40 + "\n")
        top_10 = df.sort_values('bias_mean_2024', ascending=True).head(10)
        for i, (_, row) in enumerate(top_10.iterrows(), 1):
            f.write(f"{i}. {row['labcode']}: {row['bias_mean_2024']:.4f} ± {row['bias_std_2024']:.4f} "
                   f"(Measurements: {row['n_measurements']})\n")
        
        f.write("\n")
        
        # 后10名实验室
        f.write("BOTTOM 10 LABORATORIES (HIGHEST BIAS - 2024):\n")
        f.write("-"*40 + "\n")
        bottom_10 = df.sort_values('bias_mean_2024', ascending=False).head(10)
        for i, (_, row) in enumerate(bottom_10.iterrows(), 1):
            f.write(f"{i}. {row['labcode']}: {row['bias_mean_2024']:.4f} ± {row['bias_std_2024']:.4f} "
                   f"(Measurements: {row['n_measurements']})\n")
    
    print(f"Summary report saved: {summary_file}")

def analyze_all_projects_2024():
    """
    分析所有指定的项目（仅2024年）
    """
    print("="*70)
    print("Project-Specific Laboratory Bias Analysis (2024 Only)")
    print("Calculating average absolute relative bias for each lab in 2024")
    print("="*70)
    
    # 定义要分析的项目
    projects = [
        'H-3 Beta Water',
        'Sr-90 Beta Water', 
        'Cs-137 Gamma Soil'
    ]
    
    all_project_results = []
    
    for project in projects:
        print(f"\n{'='*40}")
        print(f"Starting analysis for: {project} (2024)")
        print(f"{'='*40}")
        
        # 分析项目
        result = analyze_project_2024(project)
        
        if result is not None:
            df, project_files = result
            
            if df is not None and len(df) > 0:
                # 创建图表和报告
                create_project_analysis_chart_2024(project, df, project_files)
                
                # 保存结果用于总体比较
                all_project_results.append((project, df))
                
                # 显示简要统计信息
                print(f"\n{project} - 2024 Summary Statistics:")
                print(f"  Total laboratories: {len(df)}")
                print(f"  Average bias: {df['bias_mean_2024'].mean():.4f}")
                print(f"  Best lab: {df.iloc[0]['labcode']} ({df.iloc[0]['bias_mean_2024']:.4f})")
                print(f"  Worst lab: {df.iloc[-1]['labcode']} ({df.iloc[-1]['bias_mean_2024']:.4f})")
                
                # 显示特殊实验室信息
                special_df = df[df['is_special']]
                if not special_df.empty:
                    print(f"  Special laboratory:")
                    for _, row in special_df.iterrows():
                        print(f"    {row['labcode']}: Rank {row['rank_2024']}, "
                              f"Bias: {row['bias_mean_2024']:.4f}±{row['bias_std_2024']:.4f}")
        else:
            print(f"No data found for project: {project}")
    
    # 如果所有项目都有数据，创建跨项目比较
    if len(all_project_results) >= 2:
        create_cross_project_comparison_2024(all_project_results)
    
    print(f"\n{'='*70}")
    print("2024 Project Analyses Complete!")
    print("Results saved in individual project folders:")
    for project in projects:
        folder_name = f"project_analysis_2024_{project.replace(' ', '_').replace('-', '_')}"
        print(f"  {folder_name}/")
    print(f"{'='*70}")

def create_cross_project_comparison_2024(project_results):
    """
    创建跨项目比较图表（2024年）
    """
    print("\nCreating cross-project comparison for 2024...")
    
    # 创建比较文件夹
    comparison_folder = "project_comparison_2024"
    if not os.path.exists(comparison_folder):
        os.makedirs(comparison_folder)
    
    # 收集数据
    comparison_data = []
    
    for project_name, df in project_results:
        stats = {
            'Project': project_name,
            'Total Labs': len(df),
            'Avg Bias': df['bias_mean_2024'].mean(),
            'Min Bias': df['bias_mean_2024'].min(),
            'Max Bias': df['bias_mean_2024'].max(),
            'Std Bias': df['bias_mean_2024'].std(),
            'Avg Measurements': df['n_measurements'].mean()
        }
        comparison_data.append(stats)
    
    # 转换为DataFrame
    comp_df = pd.DataFrame(comparison_data)
    
    # 创建比较图表
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 图表1：实验室数量和平均偏差
    ax1 = axes[0, 0]
    x_pos = np.arange(len(comp_df))
    
    # 双Y轴
    ax1_bar = ax1.bar(x_pos - 0.2, comp_df['Total Labs'], 0.4, 
                     alpha=0.7, color='skyblue', label='Total Labs')
    ax1.set_xlabel('Project', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Laboratories', color='skyblue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(comp_df['Project'], rotation=15)
    
    ax1_line = ax1.twinx()
    ax1_line.plot(x_pos, comp_df['Avg Bias'], 'o-', color='orange', 
                 linewidth=2, markersize=8, label='Avg Bias')
    ax1_line.set_ylabel('Average Bias', color='orange', fontsize=12)
    ax1_line.tick_params(axis='y', labelcolor='orange')
    
    ax1.set_title('Laboratory Count vs Average Bias (2024)', fontsize=14, fontweight='bold')
    
    # 图表2：偏差范围
    ax2 = axes[0, 1]
    for i, (_, row) in enumerate(comp_df.iterrows()):
        ax2.plot([i, i], [row['Min Bias'], row['Max Bias']], 
                'o-', color='red', linewidth=3, markersize=8)
        ax2.plot(i, row['Avg Bias'], 's', color='blue', markersize=10)
    
    ax2.set_xlabel('Project', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Bias Range', fontsize=12, fontweight='bold')
    ax2.set_title('Bias Range by Project (2024)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(comp_df['Project'], rotation=15)
    ax2.grid(True, alpha=0.3)
    ax2.legend(['Bias Range', 'Average Bias'])
    
    # 图表3：参与情况
    ax3 = axes[1, 0]
    ax3.bar(x_pos, comp_df['Avg Measurements'], 
           alpha=0.7, color='green', label='Avg Measurements')
    
    ax3.set_xlabel('Project', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Average Measurements per Lab', fontsize=12, fontweight='bold')
    ax3.set_title('Participation Statistics (2024)', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(comp_df['Project'], rotation=15)
    ax3.grid(True, alpha=0.3)
    
    # 为每个柱子添加数值标签
    for i, avg_meas in enumerate(comp_df['Avg Measurements']):
        ax3.text(i, avg_meas + 0.1, f'{avg_meas:.1f}', 
                ha='center', va='bottom', fontsize=10)
    
    # 图表4：数据表格
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # 准备表格数据
    table_data = []
    for _, row in comp_df.iterrows():
        table_data.append([
            row['Project'],
            f"{row['Total Labs']}",
            f"{row['Avg Bias']:.3f}",
            f"{row['Min Bias']:.3f}",
            f"{row['Max Bias']:.3f}",
            f"{row['Avg Measurements']:.1f}"
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Project', 'Labs', 'Avg Bias', 'Min', 'Max', 'Avg Meas'],
                     cellLoc='center',
                     loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # 设置表格样式
    for i in range(len(table_data) + 1):
        for j in range(len(table_data[0])):
            cell = table[i, j]
            cell.set_edgecolor('black')
            if i == 0:
                cell.set_facecolor('#DDDDDD')
                cell.set_text_props(weight='bold')
    
    ax4.set_title('2024 Project Comparison Summary', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # 保存比较图表
    output_file = f"{comparison_folder}/project_comparison_summary_2024.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Comparison chart saved: {output_file}")
    
    # 保存比较数据
    comp_csv = f"{comparison_folder}/project_comparison_data_2024.csv"
    comp_df.to_csv(comp_csv, index=False, encoding='utf-8-sig')
    print(f"Comparison data saved: {comp_csv}")

def main():
    """
    主函数：分析所有指定项目的2024年实验室偏差
    """
    analyze_all_projects_2024()

if __name__ == "__main__":
    main()