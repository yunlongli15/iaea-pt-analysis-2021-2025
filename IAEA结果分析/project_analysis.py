import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def create_project_specific_plots():
    """
    为每个历年都有的项目创建单独的图表
    每个项目的图表显示历年难度系数和合格率变化
    """
    
    # 定义要分析的年份
    years = [2021, 2022, 2023, 2024]
    
    # 各年份参与总数
    yearly_total_participants = {
        2021: 326,
        2022: 287,
        2023: 316,
        2024: 476
    }
    
    # 基础文件夹名称
    base_folder_name = "merged_labcode_tables"
    
    # 创建一个新文件夹来存储项目图表
    output_folder = "project_analysis_charts"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    print(f"创建输出文件夹: {output_folder}")
    
    # 第一步：收集所有年份的数据
    print("\n" + "="*60)
    print("开始收集各年份数据...")
    print("="*60)
    
    all_years_data = {}
    all_projects = {}  # 存储每个项目在各年份的数据
    
    for year in years:
        folder_path = f"{base_folder_name}_{year}"
        
        if not os.path.exists(folder_path):
            print(f"警告: 文件夹 '{folder_path}' 不存在，跳过 {year} 年")
            continue
        
        print(f"\n处理 {year} 年数据...")
        year_data = []
        
        for file_name in os.listdir(folder_path):
            if file_name.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(folder_path, file_name)
                
                try:
                    df = pd.read_excel(file_path)
                    
                    # 确定评分列
                    score_column = None
                    if 'Final Score' in df.columns:
                        score_column = 'Final Score'
                    elif 'Z-Score Evaluation' in df.columns:
                        score_column = 'Z-Score Evaluation'
                    else:
                        continue
                    
                    # 提取项目名称
                    parts = file_name.split('_')
                    if len(parts) >= 3:
                        project_name_parts = parts[-3:]
                    else:
                        project_name_parts = parts
                    
                    project_name = ' '.join(project_name_parts).replace('.xlsx', '').replace('.xls', '')
                    
                    # 统计信息
                    total_participants = len(df)
                    a_count = df[score_column].str.upper().eq('A').sum()
                    
                    # 计算难度系数和合格率
                    total_year_participants = yearly_total_participants.get(year, 0)
                    difficulty = 1 - (a_count / total_year_participants) if total_year_participants > 0 else 0
                    pass_rate = a_count / total_participants if total_participants > 0 else 0
                    
                    # 存储项目数据
                    project_data = {
                        'Year': year,
                        'Project Name': project_name,
                        'File Name': file_name,
                        'Total Participants': total_participants,
                        'A Count': a_count,
                        'Difficulty Coefficient': difficulty,
                        'Pass Rate': pass_rate,
                        'Score Column': score_column
                    }
                    
                    year_data.append(project_data)
                    
                    # 添加到项目总数据中
                    if project_name not in all_projects:
                        all_projects[project_name] = {}
                    all_projects[project_name][year] = project_data
                    
                except Exception as e:
                    print(f"处理文件 {file_name} 时出错: {e}")
        
        if year_data:
            all_years_data[year] = pd.DataFrame(year_data)
            print(f"{year} 年处理完成: {len(year_data)} 个项目")
    
    # 第二步：找出所有年份都有的项目
    print("\n" + "="*60)
    print("识别历年都有的项目...")
    print("="*60)
    
    # 找出在每个年份都出现的项目
    common_projects = []
    project_years = {}
    
    for project_name in all_projects.keys():
        project_years_set = set(all_projects[project_name].keys())
        if set(years).issubset(project_years_set):
            common_projects.append(project_name)
            project_years[project_name] = sorted(list(project_years_set))
    
    print(f"找到 {len(common_projects)} 个历年都有的项目:")
    for i, project in enumerate(common_projects[:20], 1):  # 只显示前20个
        print(f"  {i:2d}. {project}")
    if len(common_projects) > 20:
        print(f"  ... 还有 {len(common_projects) - 20} 个项目")
    
    # 第三步：为每个历年都有的项目创建图表
    print("\n" + "="*60)
    print("开始为每个项目创建图表...")
    print("="*60)
    
    all_project_stats = []
    
    for project_idx, project_name in enumerate(common_projects, 1):
        print(f"处理项目 {project_idx}/{len(common_projects)}: {project_name}")
        
        # 收集该项目各年份的数据
        project_year_data = []
        for year in years:
            if year in all_projects[project_name]:
                data = all_projects[project_name][year]
                project_year_data.append({
                    'Year': year,
                    'Difficulty': data['Difficulty Coefficient'],
                    'Pass Rate': data['Pass Rate'],
                    'Participants': data['Total Participants'],
                    'A Count': data['A Count']
                })
        
        if len(project_year_data) < len(years):
            print(f"  ⚠ 项目 {project_name} 缺少某些年份数据，跳过")
            continue
        
        # 转换为DataFrame并排序
        df_project = pd.DataFrame(project_year_data)
        df_project = df_project.sort_values('Year')
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # 图表1: 难度系数变化
        years_list = df_project['Year'].tolist()
        difficulty_list = df_project['Difficulty'].tolist()
        
        bars = ax1.bar(range(len(years_list)), difficulty_list, 
                      color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], 
                      alpha=0.7, edgecolor='black')
        
        ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Difficulty Coefficient', fontsize=12, fontweight='bold', color='#1f77b4')
        ax1.set_xticks(range(len(years_list)))
        ax1.set_xticklabels(years_list, fontsize=11)
        ax1.set_title(f'Difficulty Coefficient Trend: {project_name}', 
                     fontsize=13, fontweight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 添加数值标签
        for bar, value in zip(bars, difficulty_list):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=10)
        
        # 图表2: 合格率变化
        pass_rate_list = df_project['Pass Rate'].tolist()
        
        line = ax2.plot(range(len(years_list)), pass_rate_list, 
                       color='#d62728', marker='o', markersize=8, 
                       linewidth=2.5, label='Pass Rate')
        
        ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Pass Rate', fontsize=12, fontweight='bold', color='#d62728')
        ax2.set_xticks(range(len(years_list)))
        ax2.set_xticklabels(years_list, fontsize=11)
        ax2.set_title(f'Pass Rate Trend: {project_name}', 
                     fontsize=13, fontweight='bold', pad=15)
        ax2.grid(alpha=0.3, linestyle='--')
        ax2.set_ylim([0, 1.1])
        
        # 添加数值标签
        for i, (x, y) in enumerate(zip(range(len(years_list)), pass_rate_list)):
            ax2.text(x, y + 0.03, f'{y:.3f}', ha='center', va='bottom', fontsize=10)
        
        # 添加参与人数信息
        participants_text = "Participants each year:\n"
        for idx, row in df_project.iterrows():
            participants_text += f"{int(row['Year'])}: {int(row['Participants'])} labs, {int(row['A Count'])} A's\n"
        
        fig.text(0.02, 0.02, participants_text.strip(), 
                fontsize=9, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.15, 1, 0.95])  # 为底部文本留出空间
        
        # 保存图表
        # 创建安全的文件名（移除特殊字符）
        safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_project_name = safe_project_name[:50]  # 限制文件名长度
        
        output_filename = f"{output_folder}/project_{project_idx:03d}_{safe_project_name}.png"
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close(fig)  # 关闭图形以节省内存
        
        # 收集统计信息
        avg_difficulty = df_project['Difficulty'].mean()
        avg_pass_rate = df_project['Pass Rate'].mean()
        total_participants = df_project['Participants'].sum()
        total_a_count = df_project['A Count'].sum()
        
        all_project_stats.append({
            'Project Index': project_idx,
            'Project Name': project_name,
            'Avg Difficulty': avg_difficulty,
            'Avg Pass Rate': avg_pass_rate,
            'Total Participants': total_participants,
            'Total A Count': total_a_count,
            'Overall Pass Rate': total_a_count / total_participants if total_participants > 0 else 0
        })
    
    # 第四步：创建项目统计摘要
    print("\n" + "="*60)
    print("创建项目统计摘要...")
    print("="*60)
    
    if all_project_stats:
        stats_df = pd.DataFrame(all_project_stats)
        
        # 按平均难度排序
        stats_df_sorted = stats_df.sort_values('Avg Difficulty', ascending=False)
        
        # 保存统计摘要
        stats_csv = f"{output_folder}/project_statistics_summary.csv"
        stats_df_sorted.to_csv(stats_csv, index=False, encoding='utf-8-sig')
        print(f"项目统计摘要已保存到: {stats_csv}")
        
        # 显示前10个最难的项目
        print("\n" + "-"*60)
        print("前10个最困难的项目 (按平均难度系数排序):")
        print("-"*60)
        print(stats_df_sorted.head(10)[['Project Index', 'Project Name', 
                                        'Avg Difficulty', 'Avg Pass Rate', 
                                        'Overall Pass Rate']].to_string(index=False))
        
        # 创建汇总图表
        create_summary_chart(stats_df_sorted, output_folder)
    
    print(f"\n{'='*60}")
    print("处理完成!")
    print(f"共处理 {len(common_projects)} 个历年都有的项目")
    print(f"所有图表已保存到 '{output_folder}' 文件夹")
    print(f"{'='*60}")

def create_summary_chart(stats_df, output_folder):
    """创建项目难度汇总图表"""
    if len(stats_df) < 2:
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 图表1: 各项目平均难度系数
    project_indices = stats_df['Project Index'].tolist()
    project_names_short = [name[:30] + "..." if len(name) > 30 else name 
                          for name in stats_df['Project Name'].tolist()]
    
    x_pos = np.arange(len(stats_df))
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(stats_df)))
    
    bars = ax1.barh(x_pos, stats_df['Avg Difficulty'], color=colors, alpha=0.7)
    ax1.set_yticks(x_pos)
    ax1.set_yticklabels(project_indices, fontsize=9)
    ax1.set_xlabel('Average Difficulty Coefficient', fontsize=11)
    ax1.set_title('Average Difficulty Coefficient by Project (Sorted by Difficulty)', 
                 fontsize=13, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3, linestyle='--')
    
    # 添加项目名称标签
    for i, (bar, name) in enumerate(zip(bars, project_names_short)):
        ax1.text(0.02, bar.get_y() + bar.get_height()/2, 
                f"{project_indices[i]}: {name}", 
                va='center', ha='left', fontsize=8)
    
    # 图表2: 难度系数 vs 合格率散点图
    scatter = ax2.scatter(stats_df['Avg Difficulty'], stats_df['Avg Pass Rate'],
                         c=stats_df['Overall Pass Rate'], cmap='RdYlGn',
                         s=100, alpha=0.7, edgecolors='black')
    
    ax2.set_xlabel('Average Difficulty Coefficient', fontsize=11)
    ax2.set_ylabel('Average Pass Rate', fontsize=11)
    ax2.set_title('Difficulty vs Pass Rate Correlation', fontsize=13, fontweight='bold')
    ax2.grid(alpha=0.3, linestyle='--')
    
    # 添加颜色条
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Overall Pass Rate', fontsize=10)
    
    # 添加回归线
    if len(stats_df) > 1:
        z = np.polyfit(stats_df['Avg Difficulty'], stats_df['Avg Pass Rate'], 1)
        p = np.poly1d(z)
        ax2.plot(stats_df['Avg Difficulty'], p(stats_df['Avg Difficulty']), 
                "r--", alpha=0.5, label=f'Linear fit (r={np.corrcoef(stats_df["Avg Difficulty"], stats_df["Avg Pass Rate"])[0,1]:.2f})')
        ax2.legend()
    
    plt.tight_layout()
    plt.savefig(f"{output_folder}/projects_summary_analysis.png", dpi=300, bbox_inches='tight')
    plt.close(fig)

if __name__ == "__main__":
    create_project_specific_plots()