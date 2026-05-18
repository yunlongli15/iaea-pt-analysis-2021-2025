import pandas as pd
import os
import re
from typing import List, Tuple

def extract_tables_from_excel(input_file, output_folder):
    """
    从Excel文件中提取表格数据并保存为单独的Excel文件
    
    参数:
    input_file: 输入Excel文件路径
    output_folder: 输出文件夹路径
    """
    
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 读取Excel文件
    try:
        df = pd.read_excel(input_file, header=None)
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return
    
    # 初始化变量
    all_tables_data = []  # 存储所有提取的表格数据
    current_table_data = None
    table_found = False
    table_name = ""
    headers = []
    labcode_started = False
    labcode_data = []
    table_data_start = False
    
    # 遍历所有行
    for idx, row in df.iterrows():
        row_data = row.tolist()
        
        # 检查是否是表头行（包含"TABLE"关键字）
        if any(isinstance(cell, str) and 'TABLE' in str(cell) for cell in row_data):
            # 处理前一个表格（如果有）
            if current_table_data is not None and table_found:
                # 保存当前表格数据到列表
                current_table_data['labcode_data'] = labcode_data
                all_tables_data.append(current_table_data)
            
            # 重置状态，开始新表格
            current_table_data = {
                'data_rows': [],
                'labcode_data': [],
                'headers': [],
                'name': "",
                'first_labcode': None,
                'last_labcode': None
            }
            labcode_data = []
            headers = []
            labcode_started = False
            table_found = True
            table_data_start = False
            table_name = extract_table_name(row_data)
            current_table_data['name'] = table_name
            continue
        
        # 如果已经找到表格，开始收集数据
        if table_found:
            # 检查是否是数据表头行（包含"Reported value"等关键词）
            if is_data_header(row_data):
                headers = row_data
                current_table_data['headers'] = headers
                table_data_start = True
                continue
            
            # 检查是否是Labcode行（包含"Labcode"关键字）
            if not labcode_started and any(isinstance(cell, str) and 'Labcode' in str(cell) for cell in row_data):
                labcode_started = True
                table_data_start = False
                # 不将"Labcode"文本添加到数据中
                continue
            
            # 如果Labcode已开始，收集Labcode数据
            if labcode_started:
                # 检查是否遇到新表格或文件结束
                if is_new_table_start(row_data):
                    # 保存当前表格数据到列表
                    current_table_data['labcode_data'] = labcode_data
                    all_tables_data.append(current_table_data)
                    
                    # 重置状态，开始新表格
                    current_table_data = {
                        'data_rows': [],
                        'labcode_data': [],
                        'headers': [],
                        'name': "",
                        'first_labcode': None,
                        'last_labcode': None
                    }
                    labcode_data = []
                    headers = []
                    labcode_started = False
                    table_found = True
                    table_data_start = False
                    table_name = extract_table_name(row_data)
                    current_table_data['name'] = table_name
                    continue
                
                # 检查Labcode数据行是否有效
                if is_valid_labcode_row(row_data):
                    labcode_value = extract_labcode_value(row_data[0])
                    if labcode_value is not None:
                        labcode_data.append([labcode_value])
                        
                        # 更新第一个和最后一个Labcode
                        if current_table_data['first_labcode'] is None:
                            current_table_data['first_labcode'] = labcode_value
                        current_table_data['last_labcode'] = labcode_value
                continue
            
            # 收集数据行（跳过空行或纯文本行）
            if table_data_start and is_valid_data_row(row_data):
                current_table_data['data_rows'].append(row_data)
    
    # 处理最后一个表格
    if current_table_data is not None and table_found:
        current_table_data['labcode_data'] = labcode_data
        all_tables_data.append(current_table_data)
    
    # 处理并合并表格
    process_and_merge_tables(all_tables_data, output_folder)

def extract_labcode_value(cell):
    """从单元格中提取Labcode数值"""
    if pd.isna(cell):
        return None
    
    try:
        if isinstance(cell, (int, float)):
            return int(cell)
        elif isinstance(cell, str):
            # 移除可能的空白字符，然后转换为整数
            cleaned = cell.strip()
            if cleaned.isdigit():
                return int(cleaned)
    except (ValueError, TypeError):
        return None
    
    return None

def process_and_merge_tables(all_tables_data, output_folder):
    """处理并合并表格数据"""
    if not all_tables_data:
        print("没有找到可处理的表格数据")
        return
    
    merged_tables = []
    current_merged_table = None
    table_count = 0
    
    for i, table_data in enumerate(all_tables_data):
        # 检查是否有有效的数据
        if not table_data['data_rows']:
            print(f"跳过表格 '{table_data['name']}'：缺少数据行")
            continue
            
        if not table_data['labcode_data']:
            print(f"跳过表格 '{table_data['name']}'：缺少Labcode数据")
            continue
        
        # 如果是第一个表格，创建新的合并表格
        if current_merged_table is None:
            current_merged_table = {
                'tables': [table_data],
                'name': table_data['name'],
                'first_labcode': table_data['first_labcode'],
                'last_labcode': table_data['last_labcode']
            }
            continue
        
        # 检查当前表格是否可以合并到前一个表格
        can_merge = False
        if (table_data['first_labcode'] is not None and 
            current_merged_table['last_labcode'] is not None and
            table_data['first_labcode'] > current_merged_table['last_labcode']):
            can_merge = True
        
        if can_merge:
            # 合并表格
            current_merged_table['tables'].append(table_data)
            current_merged_table['last_labcode'] = table_data['last_labcode']
            # 简化合并后的表格名称
            if '_merged_with_' not in current_merged_table['name']:
                current_merged_table['name'] = f"{current_merged_table['name']}_merged"
        else:
            # 保存当前的合并表格
            save_merged_table(current_merged_table, output_folder, table_count)
            table_count += 1
            
            # 开始新的合并表格
            current_merged_table = {
                'tables': [table_data],
                'name': table_data['name'],
                'first_labcode': table_data['first_labcode'],
                'last_labcode': table_data['last_labcode']
            }
    
    # 保存最后一个合并表格
    if current_merged_table is not None:
        save_merged_table(current_merged_table, output_folder, table_count)

def save_merged_table(merged_table_data, output_folder, table_count):
    """保存合并后的表格"""
    if not merged_table_data['tables']:
        return
    
    # 如果是单个表格，直接保存
    if len(merged_table_data['tables']) == 1:
        table_data = merged_table_data['tables'][0]
        processed_data, processed_headers = process_table_data(
            table_data['data_rows'], 
            table_data['labcode_data'], 
            table_data['headers']
        )
        
        if processed_data:
            output_file = create_output_file(
                table_data['name'], 
                table_count, 
                output_folder, 
                is_merged=False
            )
            save_to_excel(processed_data, processed_headers, output_file, table_data['name'])
    else:
        # 合并多个表格的数据
        all_processed_data = []
        all_headers = None
        
        for table_data in merged_table_data['tables']:
            processed_data, processed_headers = process_table_data(
                table_data['data_rows'], 
                table_data['labcode_data'], 
                table_data['headers']
            )
            
            if processed_data:
                all_processed_data.extend(processed_data)
                if all_headers is None:
                    all_headers = processed_headers
        
        if all_processed_data:
            output_file = create_output_file(
                merged_table_data['name'], 
                table_count, 
                output_folder, 
                is_merged=True
            )
            save_to_excel(all_processed_data, all_headers, output_file, merged_table_data['name'])

def process_table_data(data_rows, labcode_data, headers):
    """处理表格数据，合并Labcode"""
    if not data_rows or not labcode_data:
        return [], []
    
    # 检查数据行数和Labcode数据行数是否匹配
    if len(data_rows) != len(labcode_data):
        print(f"警告: 数据行数({len(data_rows)})与Labcode行数({len(labcode_data)})不匹配")
        # 使用较短的长度
        min_rows = min(len(data_rows), len(labcode_data))
        data_rows = data_rows[:min_rows]
        labcode_data = labcode_data[:min_rows]
    
    # 创建新的数据列表，将Labcode作为第一列
    processed_data = []
    for i, data_row in enumerate(data_rows):
        new_row = []
        
        # 添加Labcode（只取第一个元素）
        if i < len(labcode_data) and len(labcode_data[i]) > 0:
            labcode = labcode_data[i][0]
            if pd.isna(labcode):
                new_row.append('')
            else:
                new_row.append(labcode)
        else:
            new_row.append('')
        
        # 添加原始数据
        new_row.extend(data_row)
        processed_data.append(new_row)
    
    # 处理表头 - 添加"Labcode"作为第一列
    processed_headers = ['Labcode']
    if headers:
        for header in headers:
            if pd.isna(header):
                processed_headers.append('')
            else:
                processed_headers.append(str(header).strip())
    
    return processed_data, processed_headers

def create_output_file(table_name, table_count, output_folder, is_merged=False):
    """创建输出文件名"""
    # 简化表格名称
    if 'TABLE' in table_name:
        # 提取TABLE后面的内容
        match = re.search(r'TABLE\s+\d+[.:]\s*(.+)', table_name)
        if match:
            table_name = match.group(1).strip()
    
    safe_table_name = re.sub(r'[^\w\s-]', '', table_name)
    safe_table_name = re.sub(r'[-\s]+', '_', safe_table_name)
    safe_table_name = safe_table_name.strip('_')
    
    if not safe_table_name:
        safe_table_name = f"Table_{table_count + 1}"
    
    prefix = "merged_" if is_merged else ""
    output_file = os.path.join(output_folder, f"{table_count + 1:02d}_{prefix}{safe_table_name}.xlsx")
    
    return output_file

def save_to_excel(data, headers, output_file, table_name):
    """保存数据到Excel文件"""
    try:
        df_table = pd.DataFrame(data, columns=headers)
        df_table.to_excel(output_file, index=False)
        print(f"已保存: {output_file} ({len(data)}行数据)")
    except Exception as e:
        print(f"保存表格时出错 {table_name}: {e}")

def is_new_table_start(row_data):
    """检查是否是新表格的开始"""
    return any(isinstance(cell, str) and 'TABLE' in str(cell) for cell in row_data)

def is_valid_labcode_row(row_data):
    """检查是否是有效的Labcode数据行"""
    # 检查是否为空行
    if all(pd.isna(cell) for cell in row_data):
        return False
    
    # 检查第一个单元格是否包含Labcode数据（数字）
    if len(row_data) > 0:
        cell = row_data[0]
        if pd.isna(cell):
            return False
        
        # 尝试将第一个单元格转换为数字
        try:
            if isinstance(cell, (int, float)):
                return True
            elif isinstance(cell, str):
                cleaned = cell.strip()
                if cleaned.isdigit():
                    return True
        except:
            pass
    
    return False

def extract_table_name(row_data):
    """从行数据中提取表格名称"""
    for cell in row_data:
        if isinstance(cell, str) and 'TABLE' in cell:
            return cell.strip()
    return ""

def is_data_header(row_data):
    """检查是否是数据表头行"""
    header_keywords = ['Reported value', 'Relative bias', 'P-Test', 'Trueness', 'Precision', 'Final Score']
    
    for cell in row_data:
        if isinstance(cell, str):
            cell_lower = cell.lower()
            if any(keyword.lower() in cell_lower for keyword in header_keywords):
                return True
    return False

def is_valid_data_row(row_data):
    """检查是否是有效的数据行"""
    # 检查是否为空行
    if all(pd.isna(cell) for cell in row_data):
        return False
    
    # 检查是否包含明显的文本内容
    text_keywords = ['Reported Results', 'Target values', 'Parameter', 'Value', 
                     'Maximum Acceptable', 'Accepted', 'Warning', 'Not Accepted',
                     'FIGURE', 'Laboratory code', 'Percentage']
    
    for cell in row_data:
        if isinstance(cell, str):
            if any(keyword in cell for keyword in text_keywords):
                return False
    
    # 检查是否至少有一个数值数据
    has_numeric = False
    for cell in row_data:
        if isinstance(cell, (int, float, complex)) and not pd.isna(cell):
            has_numeric = True
        elif isinstance(cell, str):
            # 尝试将字符串转换为数值
            try:
                float(cell)
                has_numeric = True
            except ValueError:
                # 检查是否包含字母A, N, W（评价结果）
                if cell.strip() in ['A', 'N', 'W']:
                    has_numeric = True
    
    return has_numeric

def main():
    # 输入文件路径
    input_file = "IAEA-TERC-2023-01_summary_report.xlsx"
    
    # 输出文件夹路径
    output_folder = "merged_labcode_tables_2023"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        return
    
    print(f"开始处理文件: {input_file}")
    print(f"输出文件夹: {output_folder}")
    print("-" * 50)
    
    # 提取表格
    extract_tables_from_excel(input_file, output_folder)
    
    print("-" * 50)
    print("处理完成！")

if __name__ == "__main__":
    main()