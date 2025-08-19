import json
import os
import re
import csv
from typing import Dict, Any, Tuple, List, Union
import argparse

def to_hashable(obj: Any, key_name: str = None) -> Any:
    """
    Convert data structures to hashable types for duplicate detection.
    
    This function handles nested dictionaries, lists, and special numeric patterns
    used in puzzle configuration data. It ensures consistent comparison by
    converting complex structures to hashable tuples.
    
    Args:
        obj: The object to convert (dict, list, tuple, or primitive type)
        key_name: Name of the current key being processed (used for special handling)
        
    Returns:
        Hashable representation of the input object
    """
    if isinstance(obj, dict):
        return tuple(sorted((k, to_hashable(v, key_name=k)) for k, v in obj.items()))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        processed_items = []
        for item in obj:
            if isinstance(item, (list, tuple)):
                processed_items.append(tuple(to_hashable(subitem, key_name=None) for subitem in item))
            else:
                processed_items.append(to_hashable(item, key_name=None))
        
        if key_name == "pool" and any(isinstance(item, tuple) for item in processed_items):
            return tuple(sorted(processed_items))
        else:
            return tuple(processed_items)
    elif isinstance(obj, str) and re.match(r"^__(\d+)__$", obj):
        return int(re.match(r"^__(\d+)__$", obj).group(1))
    elif isinstance(obj, str) and re.match(r"^__(\d+\.\d+)__$", obj):
        return float(re.match(r"^__(\d+\.\d+)__$", obj).group(1))
    else:
        return obj

def is_numeric_value(value: Any) -> bool:
    """
    Check if a value represents numeric data, including special patterns.
    
    This function identifies values that should be considered for duplicate
    detection based on their numeric content, including special encoded patterns.
    
    Args:
        value: Value to check for numeric nature
        
    Returns:
        True if the value represents numeric data, False otherwise
    """
    if isinstance(value, (int, float)):
        return True
    elif isinstance(value, list):
        # Recursively check list elements
        return all(is_numeric_value(item) for item in value)
    elif isinstance(value, str) and re.match(r"^__(\d+(\.\d+)?)__$", value):
        # Special numeric pattern strings
        return True
    elif isinstance(value, tuple):
        # Recursively check tuple elements
        return all(is_numeric_value(item) for item in value)
    elif isinstance(value, dict):
        # Nested dictionaries need recursive processing
        return True
    return False

def extract_numeric_values(config: Dict[str, Any], prefix: str = "") -> List[Tuple[str, Any]]:
    """
    Recursively extract all numeric key-value pairs from nested dictionaries.
    
    This function traverses nested configuration dictionaries and extracts
    all values that represent numeric data, creating a flattened list of
    key paths and their corresponding values.
    
    Args:
        config: Configuration dictionary to process
        prefix: Current key path prefix for nested traversal
        
    Returns:
        List of (key_path, hashable_value) tuples for all numeric values
    """
    numeric_items = []
    
    for key, value in config.items():
        if key == '_query':
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        
        if is_numeric_value(value):
            if isinstance(value, dict):
                numeric_items.extend(extract_numeric_values(value, full_key))
            else:
                hashable_value = to_hashable(value, key_name=key)
                numeric_items.append((full_key, hashable_value))
    
    return numeric_items

def get_numeric_signature(config: Dict[str, Any]) -> Tuple[Tuple[str, Any]]:
    """提取config中的数值特征签名"""
    numeric_items = extract_numeric_values(config)
    numeric_items.sort(key=lambda x: x[0])
    return tuple(numeric_items)

def analyze_equivalent_configs(input_path: str) -> Dict[str, List[Tuple[Tuple, List[int]]]]:
    """
    分析文件或目录中的等价配置
    返回: {文件名: [(签名, [行号列表]), ...]}
    """
    results = {}
    
    if os.path.isfile(input_path) and input_path.endswith('.jsonl'):
        filename = os.path.basename(input_path)
        results[filename] = analyze_single_file(input_path)
        return results
    
    if os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            if filename.endswith('.jsonl'):
                file_path = os.path.join(input_path, filename)
                results[filename] = analyze_single_file(file_path)
        return results
    
    raise ValueError(f"输入路径不存在或不是JSONL文件: {input_path}")

def analyze_single_file(file_path: str) -> List[Tuple[Tuple, List[int]]]:
    """分析单个文件的等价配置"""
    with open(file_path, 'r', encoding='utf-8') as infile:
        signatures_map = {}
        
        for line_number, line in enumerate(infile, start=1):
            try:
                record = json.loads(line)
                config = record.get("config", {})
                signature = get_numeric_signature(config)
                
                if signature:
                    if signature in signatures_map:
                        signatures_map[signature].append(line_number)
                    else:
                        signatures_map[signature] = [line_number]
                        
            except json.JSONDecodeError:
                continue
        
        # 只保留有重复的配置组
        return [(sig, lines) for sig, lines in signatures_map.items() if len(lines) > 1]

def generate_detailed_report(results: Dict[str, List[Tuple[Tuple, List[int]]]], output_file: str = None):
    """生成详细报告"""
    output = []
    
    for filename, groups in results.items():
        if not groups:
            output.append(f"文件 {filename}: 未发现等价配置\n")
            continue
            
        output.append(f"=== 文件 {filename} ===")
        output.append(f"总计发现 {len(groups)} 个等价组")
        output.append(f"总计 {sum(len(lines) for _, lines in groups)} 行重复数据\n")
        
        for idx, (signature, lines) in enumerate(groups, 1):
            output.append(f"等价配置组 {idx}:")
            output.append(f"  数值特征签名: {signature}")
            output.append(f"  重复行号: {lines}\n")
    
    report = "\n".join(output)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    else:
        print(report)

def generate_overview_report(results: Dict[str, List[Tuple[Tuple, List[int]]]], output_file: str):
    """生成概览CSV报告"""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['文件名', '等价配置组数', '等价数据数量'])
        
        for filename, groups in results.items():
            group_count = len(groups)
            duplicate_count = sum(len(lines) for _, lines in groups)
            writer.writerow([filename, group_count, duplicate_count])

def main():
    parser = argparse.ArgumentParser(description='检查JSONL文件中的等价配置')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # 详细模式
    detail_parser = subparsers.add_parser('detail', help='生成详细报告')
    detail_parser.add_argument('-i', '--input', required=True, help='输入文件或目录路径')
    detail_parser.add_argument('-o', '--output', help='输出文件路径（可选，不指定则打印到控制台）')
    
    # 概览模式
    overview_parser = subparsers.add_parser('overview', help='生成概览CSV报告')
    overview_parser.add_argument('-i', '--input', required=True, help='输入文件或目录路径')
    overview_parser.add_argument('-o', '--output', required=True, help='输出CSV文件路径')
    
    args = parser.parse_args()
    
    print("开始分析等价配置...")
    results = analyze_equivalent_configs(args.input)
    
    if args.command == 'detail':
        generate_detailed_report(results, args.output if 'output' in args else None)
    elif args.command == 'overview':
        generate_overview_report(results, args.output)
    
    print("分析完成！")

if __name__ == "__main__":
    main()