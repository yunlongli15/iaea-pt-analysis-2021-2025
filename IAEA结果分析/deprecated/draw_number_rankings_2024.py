import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from collections import defaultdict

def main():
    # 1. 读取所有表格文件，统计实验室参与项目数量
    lab_participation = defaultdict(int)
    
    # 查找所有Excel文件
    excel_files = glob.glob("merged_labcode_tables_2024/*.xlsx") + glob.glob("merged_labcode_tables_2024/*.xls")
    
    if not excel_files:
        print("未找到Excel文件，尝试查找CSV文件...")
        csv_files = glob.glob("merged_labcode_tables/*.csv")
        all_files = csv_files
    else:
        all_files = excel_files
    
    print(f"找到 {len(all_files)} 个分析项目文件")
    
    # 处理每个文件
    for file_path in all_files:
        try:
            # 读取文件
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, encoding='gbk')
            
            # 查找labcode列
            if 'labcode' in df.columns:
                labcode_col = 'labcode'
            elif 'Labcode' in df.columns:
                labcode_col = 'Labcode'
            elif 'LABCODE' in df.columns:
                labcode_col = 'LABCODE'
            else:
                labcode_col = df.columns[0]
            
            # 统计该文件中的实验室
            labcodes = df[labcode_col].dropna().astype(str).str.strip()
            unique_labs = set(labcodes.unique())
            
            for lab in unique_labs:
                if lab:
                    lab_participation[lab] += 1
                    
        except Exception as e:
            print(f"处理文件 {os.path.basename(file_path)} 时出错: {e}")
    
    # 2. 转换为DataFrame并按参与数量排序
    df = pd.DataFrame(list(lab_participation.items()), 
                      columns=['labcode', 'count'])
    df = df.sort_values('count', ascending=False)  # 降序排列，参与最多的在最左边
    df['x'] = range(len(df))
    
    # 3. 特别标注labcode5
    df['is_special'] = False
    df['color'] = 'skyblue'
    df['size'] = 10
    
    special_mask = df['labcode'].astype(str).str.strip().str.lower().isin(['5', 'lab5', 'labcode5', 'lab005'])
    df.loc[special_mask, 'is_special'] = True
    df.loc[special_mask, 'color'] = 'red'
    df.loc[special_mask, 'size'] = 40
    
    # 4. 创建散点图
    plt.figure(figsize=(18, 8))
    
    # 绘制散点
    plt.scatter(df['x'], df['count'], 
                s=df['size'], 
                c=df['color'], 
                alpha=0.7, 
                edgecolors='black', 
                linewidths=0.5,
                zorder=5)  # 确保散点在网格线上方
    
    # 设置x轴标签 - 全部显示，小字体，90度倾斜
    plt.xticks(df['x'], df['labcode'], rotation=90, ha='right', fontsize=3)
    
    # 设置坐标轴标签
    plt.xlabel('Laboratory code', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Analysis Projects', fontsize=12, fontweight='bold')
    
    # 添加网格（只显示y轴方向的网格线）
    plt.grid(True, axis='y', alpha=0.3, linestyle='--', zorder=0)
    
    # 调整x轴范围，为标签留出空间
    plt.xlim(-1, len(df))
    
    # 调整y轴范围
    y_max = df['count'].max()
    plt.ylim(0, y_max * 1.05)
    
    # 为特别标注的实验室添加标签
    special_labs = df[df['is_special']]
    for _, row in special_labs.iterrows():
        plt.annotate(f"{row['labcode']}",
                    xy=(row['x'], row['count']),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=9,
                    fontweight='bold',
                    color='red',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7, edgecolor='red'))
    
    # 调整布局，为x轴标签留出更多空间
    plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.95])
    
    # 保存图片
    plt.savefig('labcode_participation_scatter.png', dpi=300, bbox_inches='tight')
    
    # 显示图片
    plt.show()
    
    # 5. 打印简要统计信息
    print(f"\n统计完成:")
    print(f"总实验室数量: {len(df)}")
    print(f"总分析项目数: {len(all_files)}")
    
    # 显示前10名
    print(f"\n参与项目最多的前10个实验室:")
    for i, row in df.head(10).iterrows():
        special_mark = " ★" if row['is_special'] else ""
        print(f"  {i+1}. {row['labcode']}{special_mark}: {row['count']} 个项目")
    
    # 显示labcode5的排名
    special_labs = df[df['is_special']]
    if not special_labs.empty:
        print(f"\n特别标注的实验室:")
        for _, row in special_labs.iterrows():
            rank = df[df['count'] >= row['count']].shape[0]
            print(f"  {row['labcode']}: 排名第{rank}，参与{row['count']}个项目")

if __name__ == "__main__":
    main()