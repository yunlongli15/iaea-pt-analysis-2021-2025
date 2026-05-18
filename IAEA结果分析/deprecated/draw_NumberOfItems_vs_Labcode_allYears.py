import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

def process_year_data(year, labcode_order):
    """处理指定年份的数据，按给定的labcode顺序对齐"""
    lab_participation = defaultdict(int)
    
    # 根据年份构建文件路径模式
    folder_pattern = f"merged_labcode_tables_{year}"
    
    # 查找所有文件
    excel_files = glob.glob(f"{folder_pattern}/*.xlsx") + glob.glob(f"{folder_pattern}/*.xls")
    
    if not excel_files:
        print(f"{year}年: 未找到Excel文件，尝试查找CSV文件...")
        csv_files = glob.glob(f"{folder_pattern}/*.csv")
        all_files = csv_files
    else:
        all_files = excel_files
    
    print(f"{year}年: 找到 {len(all_files)} 个分析项目文件")
    
    # 处理每个文件
    for file_path in all_files:
        try:
            # 读取文件
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                # 尝试不同的编码
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    df = pd.read_csv(file_path, encoding='gbk')
            
            # 查找labcode列
            labcode_col = None
            for col_name in ['labcode', 'Labcode', 'LABCODE']:
                if col_name in df.columns:
                    labcode_col = col_name
                    break
            
            if labcode_col is None:
                # 查找包含labcode的列名
                for col in df.columns:
                    if 'labcode' in str(col).lower():
                        labcode_col = col
                        break
                if labcode_col is None:
                    labcode_col = df.columns[0]
            
            # 统计该文件中的实验室
            labcodes = df[labcode_col].dropna().astype(str).str.strip()
            unique_labs = set(labcodes.unique())
            
            for lab in unique_labs:
                if lab and lab != 'nan':
                    lab_participation[lab] += 1
                    
        except Exception as e:
            print(f"{year}年: 处理文件 {os.path.basename(file_path)} 时出错: {e}")
    
    # 转换为Series，并按给定的labcode顺序对齐
    year_series = pd.Series(lab_participation)
    
    # 创建完整的数据系列（包含所有labcode，缺失的值为0）
    full_series = pd.Series(0, index=labcode_order)
    for lab in labcode_order:
        if lab in year_series:
            full_series[lab] = year_series[lab]
    
    return full_series

def main():
    # 1. 首先处理2024年的数据，确定labcode的顺序
    print("=== 处理2024年数据（确定实验室顺序）===")
    lab_participation_2024 = defaultdict(int)
    
    # 查找2024年文件
    folder_2024 = "merged_labcode_tables_2024"
    excel_files_2024 = glob.glob(f"{folder_2024}/*.xlsx") + glob.glob(f"{folder_2024}/*.xls")
    
    if not excel_files_2024:
        print("2024年: 未找到Excel文件，尝试查找CSV文件...")
        csv_files_2024 = glob.glob(f"{folder_2024}/*.csv")
        all_files_2024 = csv_files_2024
    else:
        all_files_2024 = excel_files_2024
    
    print(f"2024年: 找到 {len(all_files_2024)} 个分析项目文件")
    
    # 处理2024年每个文件
    for file_path in all_files_2024:
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    df = pd.read_csv(file_path, encoding='gbk')
            
            # 查找labcode列
            labcode_col = None
            for col_name in ['labcode', 'Labcode', 'LABCODE']:
                if col_name in df.columns:
                    labcode_col = col_name
                    break
            
            if labcode_col is None:
                for col in df.columns:
                    if 'labcode' in str(col).lower():
                        labcode_col = col
                        break
                if labcode_col is None:
                    labcode_col = df.columns[0]
            
            # 统计该文件中的实验室
            labcodes = df[labcode_col].dropna().astype(str).str.strip()
            unique_labs = set(labcodes.unique())
            
            for lab in unique_labs:
                if lab and lab != 'nan':
                    lab_participation_2024[lab] += 1
                    
        except Exception as e:
            print(f"2024年: 处理文件 {os.path.basename(file_path)} 时出错: {e}")
    
    # 转换为DataFrame并按参与数量排序
    df_2024 = pd.DataFrame(list(lab_participation_2024.items()), 
                          columns=['labcode', 'count'])
    df_2024 = df_2024.sort_values('count', ascending=False)  # 降序排列
    
    # 获取2024年的labcode顺序（按参与数量降序）
    labcode_order = df_2024['labcode'].tolist()
    
    # 2. 处理各年份数据
    print("\n=== 处理各年份数据 ===")
    years = [2021, 2022, 2023, 2024]
    
    # 存储各年份数据
    year_data = {}
    for year in years:
        if year == 2024:
            # 2024年已有数据
            year_data[year] = pd.Series(dict(zip(df_2024['labcode'], df_2024['count'])))
        else:
            year_data[year] = process_year_data(year, labcode_order)
    
    # 3. 创建DataFrame用于绘图
    plot_df = pd.DataFrame(index=labcode_order)
    for year in years:
        plot_df[f'{year}'] = year_data[year]
    
    # 添加x坐标
    plot_df['x'] = range(len(plot_df))
    
    # 4. 特别标注labcode5
    plot_df['is_special'] = False
    special_mask = plot_df.index.astype(str).str.strip().str.lower().isin(['5', 'lab5', 'labcode5', 'lab005'])
    plot_df.loc[special_mask, 'is_special'] = True
    
    # 5. 创建多系列散点图
    plt.figure(figsize=(20, 10))
    
    # 颜色和标记样式
    colors = ['skyblue', 'green', 'orange', 'red']
    markers = ['o', 'o', 'o', 'o']
    year_labels = ['2024', '2022', '2023', '2021']
    
    # 绘制每个年份的散点
    for idx, year in enumerate(years):
        plt.scatter(plot_df['x'], plot_df[f'{year}'], 
                   s=10,  # 点大小
                   c=colors[idx], 
                   marker=markers[idx],
                   alpha=0.7, 
                   edgecolors='black', 
                   linewidths=0.5,
                   label=f'{year}年',
                   zorder=5)
    
    # 6. 设置图表样式
    # x轴标签 - 使用2024年的labcode顺序
    plt.xticks(plot_df['x'], plot_df.index, rotation=90, ha='right', fontsize=3)
    
    # 设置坐标轴标签
    plt.xlabel('Laboratory Code (按2024年参与项目数量降序排列)', fontsize=14, fontweight='bold')
    plt.ylabel('Number of Analysis Projects', fontsize=14, fontweight='bold')
    
    # 添加标题
    plt.title('实验室参与分析项目数量统计 (2021-2024)', fontsize=16, fontweight='bold', pad=20)
    
    # 添加网格（只显示y轴方向的网格线）
    plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
    
    # 调整x轴范围
    plt.xlim(-1, len(plot_df))
    
    # 调整y轴范围
    y_max = plot_df[[f'{year}' for year in years]].max().max()
    plt.ylim(0, y_max * 1.1)
    
    # 添加图例
    plt.legend(loc='upper right', fontsize=12)
    
    # 7. 为特别标注的实验室添加标签
    special_labs = plot_df[plot_df['is_special']]
    for idx, row in special_labs.iterrows():
        # 获取该实验室的最高值
        max_value = max([row[f'{year}'] for year in years])
        # 找到该值对应的年份
        max_year = [year for year in years if row[f'{year}'] == max_value][0]
        
        plt.annotate(f"{idx}",
                    xy=(row['x'], max_value),
                    xytext=(0, 15),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    fontweight='bold',
                    color='red',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7, edgecolor='red'))
    
    # 调整布局
    plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])
    
    # 8. 保存图片
    plt.savefig('labcode_participation_multi_year_scatter.png', dpi=300, bbox_inches='tight')
    
    # 显示图片
    plt.show()
    
    # 9. 打印统计信息
    print("\n=== 统计信息 ===")
    print(f"总实验室数量: {len(plot_df)}")
    
    # 显示各年份的项目总数
    print("\n各年份项目总数:")
    for year in years:
        total_projects = plot_df[f'{year}'].sum()
        print(f"  {year}年: {int(total_projects)} 个项目")
    
    # 显示各年份前5名实验室
    print("\n各年份参与项目最多的前5个实验室:")
    for year in years:
        print(f"\n{year}年:")
        # 按该年份数据排序
        sorted_indices = plot_df[f'{year}'].sort_values(ascending=False).head(5).index
        for i, lab in enumerate(sorted_indices, 1):
            count = plot_df.loc[lab, f'{year}']
            special_mark = " ★" if plot_df.loc[lab, 'is_special'] else ""
            print(f"  {i}. {lab}{special_mark}: {int(count)} 个项目")

if __name__ == "__main__":
    main()