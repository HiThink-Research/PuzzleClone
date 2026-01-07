import json, yaml
import os
from typing import Dict, Any, List, Tuple
import argparse

QTYPE_LIST = ["简答题", "单选题", "多选题", "填空题", "计算题"]
EVAL_TYPE_LIST = ["nominal", "strict_nominal", "numeral", "option", "multi_options", "ordered array", "unordered array"]

def validate_nest_array_format(type_str):
    ou, ele_type = type_str.split("a_")
    if set(ou).issubset({'u', 'o'}) and ele_type in ["nominal", "numeral"]:
        return True
    return False

def validate_type(record, type: str) -> bool:
    try:
        for ti in record[type].split(','):
            val_list = QTYPE_LIST if type == 'qtype' else EVAL_TYPE_LIST
            if ti not in val_list:
                if (type == 'eval_type' and not validate_nest_array_format(ti)) or (type == 'qtype'):
                    print(f"File {type} validation error: {ti} is invalid, {type} is {record[type]}")
                    return False
    except Exception as e:
        print(f"Error: {e}\nFile {type} validation error: {record} is invalid.")
        return False
    return True


def process_jsonl_files(input_dir: str, output_dir: str, dsl_dir: str = None, add_ids: bool = False) -> int:
    """
    Process all JSONL files in a directory, adding metadata fields and calculating scale parameters.
    
    This function formats raw puzzle data by:
    1. Adding question type (qtype) and evaluation type (eval_type) metadata
    2. Calculating normalized variable scale (vars_scale) from DSL specifications
    3. Adding unique IDs if requested
    4. Adding source field based on filename
    
    Args:
        input_dir: Input directory containing raw JSONL files
        output_dir: Output directory for formatted JSONL files
        dsl_dir: DSL specification directory (optional, used for vars_scale calculation)
        add_ids: Whether to add unique ID fields (format: filename-linenumber)
    
    Returns:
        The number of successed processing files.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    success_file_num = 0
    
    # Process all files in the input directory
    for filename in os.listdir(input_dir):
        if not filename.endswith('.jsonl'):
            continue
            
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        # Extract filename (without extension) to use as source value
        source_value = os.path.splitext(filename)[0]
        
        print(f"\nProcessing file: {input_path}")
    
        qtype_value = ''
        eval_type_value = ''
        # Read first record as reference for metadata
        with open(input_path, 'r', encoding='utf-8') as infile:
            first_line = infile.readline()
            try:
                first_record = json.loads(first_line)
                if 'qtype' in first_record and 'eval_type' in first_record:
                    # Validate existing qtype and eval_type values
                    val_res = validate_type(first_record, 'qtype') and validate_type(first_record, 'eval_type')
                    if val_res:
                        print("File already contains qtype and eval_type fields, skipping addition")
                        qtype_value = first_record['qtype']
                        eval_type_value = first_record['eval_type']
                    else:
                        print("Please input the qtype and eval_type again!")
            except json.JSONDecodeError:
                print("Unable to parse first record as example")
                first_record = {}
        
        if qtype_value == '' or eval_type_value == '':
            # Get user input for qtype and eval_type for current file
            print("\nExample record for reference:")
            print("Problem: ", first_record.get("problem", ""), "Answer: ", first_record.get("answer", ""))
            print("\nValid qtype: ", ', '.join(QTYPE_LIST))
            qtype_value = input("Please enter qtype value for this file: ")
            while not validate_type({"qtype": qtype_value}, 'qtype'):
                qtype_value = input("Please enter qtype value for this file again: ")
            print("\nValid eval_type: ", ', '.join(EVAL_TYPE_LIST), "and \"x*a_y\" like ooa_numeral, ooa_nominal, and oua_nominal.")
            eval_type_value = input("Please enter eval_type value for this file: ")
            while not validate_type({"eval_type": eval_type_value}, 'eval_type'):
                eval_type_value = input("Please enter eval_type value for this file again: ")
        
        print(f"\nStarting processing {input_path} -> {output_path}")
        
        # Read all data from input file
        all_data: List[Dict[str, Any]] = []
        with open(input_path, 'r', encoding='utf-8') as infile:
            for line_number, line in enumerate(infile, 1):
                try:
                    record = json.loads(line)
                    
                    # Add unique ID if requested
                    if add_ids and 'id' not in record:
                        # Determine the required zero-padding width based on total lines
                        total_lines = sum(1 for _ in open(input_path, 'r', encoding='utf-8'))
                        width = 4 if total_lines < 10000 else len(str(total_lines))
                        line_num_str = f"{line_number:0{width}d}"
                        record['id'] = f"{source_value}-{line_num_str}"
                    
                    all_data.append(record)
                except json.JSONDecodeError as e:
                    print(f"Parse error (line {line_number}, content: {line.strip()}): {e}")
                    continue
        
        # Calculate vars_scale if DSL directory is provided
        if dsl_dir:
            # Define possible file extensions (in order of priority)
            extensions = ['.json', '.yaml', '.yml']
            dsl_file_path = None
            # Check if file exists for each extension
            for ext in extensions:
                dsl_file_path = os.path.join(dsl_dir, source_value + ext)
                if os.path.exists(dsl_file_path):
                    break
            
            # Parse DSL file to get variables that need normalization
            vars = []
            diff_factors = []
            try:
                with open(dsl_file_path, 'r', encoding='utf-8') as f:
                    if dsl_file_path.endswith(".json"):
                        dsl = json.load(f)
                    else:
                        dsl = yaml.safe_load(f)
                    if "variables" in dsl:
                        for k, v in dsl["variables"].items():
                            if "domain" in v:
                                vars.append(k)
                                diff_factors.append(v["diff_factor"] if "diff_factor" in v else 0)
                print(f"Variables requiring normalization: {vars}")
            except Exception as e:
                print(f"Error reading DSL file {dsl_file_path}: {e}")
                vars = []
            
            # Calculate min and max values for each variable
            var_min_max: Dict[str, Tuple[float, float]] = {}
            warning_flag = False
            for var in vars:
                values: List[float] = []
                for data in all_data:
                    if "config" in data and var in data["config"]:
                        if isinstance(data["config"], str):
                            if warning_flag == False:
                                warning_flag = True
                                print(f"Warning: config field is string in {input_path} (record {data.get('id', '')}), attempting to parse as JSON")
                            data["config"] = json.loads(data["config"])
                        value = data["config"][var]

                        if isinstance(value, (int, float)):
                            values.append(float(value))
                
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    var_min_max[var] = (min_val, max_val)
                    print(f"Variable {var} value range: [{min_val}, {max_val}]")
            
            # Calculate vars_scale and add to each record
            for data in all_data:
                normalized_values = []
                config = data.get("config", {})
                
                # Process each variable with its difficulty factor
                for var, diff in zip(vars, diff_factors):
                    if var in config and var in var_min_max:
                        value = config[var]
                        
                        if isinstance(value, (int, float)):
                            min_val, max_val = var_min_max[var]
                            value_range = max_val - min_val
                            
                            # Normalize value to [0, 1] range
                            if value_range > 0:
                                normalized = (value - min_val) / value_range
                            else:
                                normalized = 0.5  # Default for constant values
                            
                            # Adjust based on difficulty factor
                            if diff > 0:
                                normalized_values.append(normalized)
                            elif diff < 0:
                                normalized_values.append(1 - normalized)  # Invert for negative difficulty
                
                # Calculate average normalized scale
                if normalized_values:
                    avg_scale = sum(normalized_values) / len(normalized_values)
                else:
                    avg_scale = 0.5  # Default when no variables to normalize
                
                # Add vars_scale parameter to record
                if "parameters" not in data:
                    data["parameters"] = {}
                data["parameters"]["vars_scale"] = avg_scale
        
        # Add metadata fields to all records
        for record in all_data:
            if qtype_value:
                record["qtype"] = qtype_value
            if eval_type_value:
                record["eval_type"] = eval_type_value
            record["source"] = source_value
        
        # Write processed data to output file
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for record in all_data:
                outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
            success_file_num += 1

    return success_file_num

def main():
    """Main entry point for the data formatting tool."""
    parser = argparse.ArgumentParser(description='Format and preprocess JSONL puzzle files with metadata and variable scaling')
    parser.add_argument('-i', '--input', default='tmp', help='Input directory path (default: "tmp")')
    parser.add_argument('-o', '--output', default='.', help='Output directory path (default: current directory)')
    parser.add_argument('-d', '--dsl', help='DSL specification directory path (used for vars_scale calculation)')
    parser.add_argument('--add-ids', action='store_true', help='Add unique ID fields (format: filename-linenumber)')
    
    args = parser.parse_args()
    
    print("Starting JSONL file processing...")
    res = process_jsonl_files(args.input, args.output, args.dsl, args.add_ids)
    print(f"\nAll {res} files processed successfully!")

if __name__ == "__main__":
    main()
