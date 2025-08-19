import json
import os
import argparse
from typing import Dict, Tuple

def sort_dict_by_key(data: Dict, granularity: bool = False, switch_to_key_value: bool = True) -> Dict:
    """
    Sort and merge dictionary data for difficulty distribution analysis.
    
    This function processes difficulty distribution data by either maintaining fine-grained
    scores or merging them into 10 intervals for better visualization.
    
    Args:
        data: Dictionary containing difficulty scores as keys and counts as values
        granularity: If True, maintains fine-grained scores; if False, merges into intervals
        switch_to_key_value: If True, sorts by keys; if False, sorts by values
        
    Returns:
        Processed dictionary with sorted/merged difficulty distribution
    """
    if granularity:
        if switch_to_key_value:
            # Sort by keys (convert to float and sort in descending order)
            sorted_items = sorted(data.items(), key=lambda item: float(item[0]), reverse=True)
            return dict(sorted_items)
        else:
            # Sort by values (descending order)
            sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)
            return dict(sorted_items)
    else:
        # Merge into 10 equal intervals based on difficulty score range
        sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)
        
        float_keys = [float(key) for key, _ in sorted_items]
        
        min_key = min(float_keys)
        max_key = max(float_keys)
        interval_width = (max_key - min_key) / 10
        
        # Initialize 10 intervals
        merged_dict = {}
        for i in range(10):
            start = min_key + i * interval_width
            end = start + interval_width
            # First interval is closed on both ends, others are left-open
            interval_key = f"({start:.2f}, {end:.2f}]" if i > 0 else f"[{start:.2f}, {end:.2f}]"
            merged_dict[interval_key] = 0
        
        # Assign each score to its corresponding interval
        for key_str, value in sorted_items:
            key_float = float(key_str)
            # Find the corresponding interval index
            index = 9  # Default to last interval
            for t in range(9, -1, -1):
                if key_float <= min_key + interval_width * (t + 1):
                    index = t
            
            # Generate the interval key and accumulate count
            start = min_key + index * interval_width
            end = start + interval_width
            interval_key = f"({start:.2f}, {end:.2f}]" if index > 0 else f"[{start:.2f}, {end:.2f}]"
            merged_dict[interval_key] += value
    
    return merged_dict

def min_max_score(list_jsonl: list) -> Tuple[Tuple, Tuple, Tuple]:
    """
    Calculate min and max values for problem length, condition count, and symbol count.
    
    This function analyzes the range of key metrics used in difficulty calculation:
    - Problem text length (character count)
    - Number of conditions (cond_num parameter)
    - Number of symbols (sym_num parameter)
    
    Args:
        list_jsonl: List of JSONL file lines as strings
        
    Returns:
        Tuple containing (len_min_max, cond_min_max, sym_min_max) where each is (min, max)
    """
    list_len = []
    list_cond = []
    list_sym = []
    for line in list_jsonl:
        temp = json.loads(line)
        list_len.append(len(temp["problem"]))
        list_cond.append(temp["parameters"]["cond_num"])
        list_sym.append(temp["parameters"]["sym_num"])
    len_min_max = (min(list_len), max(list_len))
    cond_min_max = (min(list_cond), max(list_cond))
    sym_min_max = (min(list_sym), max(list_sym))
    return (len_min_max, cond_min_max, sym_min_max)

def norm_num(data: Dict, len_min_max: Tuple, cond_min_max: Tuple, sym_min_max: Tuple) -> float:
    """
    Calculate normalized difficulty score for a single data record.
    
    The difficulty score is computed as the average of four normalized metrics:
    1. Problem text length (normalized to [0,1])
    2. Number of conditions (normalized to [0,1])
    3. Number of symbols (normalized to [0,1])
    4. Variable scale (already normalized, from parameters)
    
    Args:
        data: Single data record containing problem text and parameters
        len_min_max: Tuple of (min, max) problem lengths for normalization
        cond_min_max: Tuple of (min, max) condition counts for normalization
        sym_min_max: Tuple of (min, max) symbol counts for normalization
        
    Returns:
        Normalized difficulty score in range [0,1], rounded to 3 decimal places
    """
    # Normalize problem length (handle edge case where all problems have same length)
    if len_min_max[0] == len_min_max[1]:
        len_norm = 0.5  # Assign middle value when no variation
    else:
        len_norm = (len(data["problem"])-len_min_max[0])/(len_min_max[1]-len_min_max[0])
    
    # Normalize condition count
    if cond_min_max[0] == cond_min_max[1]:
        cond_norm = 0.5  # Assign middle value when no variation
    else:
        cond_norm = (data["parameters"]["cond_num"]-cond_min_max[0])/(cond_min_max[1]-cond_min_max[0])
    
    # Normalize symbol count
    if sym_min_max[0] == sym_min_max[1]:
        sym_norm = 0.5  # Assign middle value when no variation
    else:
        sym_norm = (data["parameters"]["sym_num"]-sym_min_max[0])/(sym_min_max[1]-sym_min_max[0])
    
    # Average all four normalized metrics
    return round((len_norm+cond_norm+sym_norm+data["parameters"]["vars_scale"])/4, 3)

def generate_difficulty(data_path: str, output_path: str) -> None:
    """
    Generate difficulty scores for all JSONL files and write to output directory.
    
    This function processes all .jsonl files in the input directory, calculates
    difficulty scores for each record, and saves the enhanced data to the output directory.
    
    Args:
        data_path: Input directory containing JSONL files
        output_path: Output directory where processed files will be saved
    """
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Process all JSONL files in the input directory
    for dir_add, _, file_list in os.walk(data_path):
        for file in file_list:
            if not file.endswith('.jsonl'):
                continue
                
            print(f"Processing {file}")
            input_file = os.path.join(dir_add, file)
            output_file = os.path.join(output_path, file)
            
            # Read all lines and calculate normalization ranges
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                len_min_max, cond_min_max, sym_min_max = min_max_score(lines)
                
                # Process each line and add difficulty score
                output_lines = []
                for line in lines:
                    data = json.loads(line)
                    difficulty_score = norm_num(data, len_min_max, cond_min_max, sym_min_max)
                    data["difficulty"] = difficulty_score
                    output_lines.append(json.dumps(data, ensure_ascii=False) + '\n')
            
            # Write enhanced data to output file
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(output_lines)

def generate_distribution(data_path: str, output_file: str, granularity: bool = False, switch_to_key: bool = False) -> None:
    """
    Generate difficulty distribution statistics for all JSONL files.
    
    This function analyzes the distribution of difficulty scores across all files
    and generates comprehensive statistics including per-file and aggregate distributions.
    
    Args:
        data_path: Input directory containing JSONL files
        output_file: Output JSON file path for distribution statistics
        granularity: If True, maintains fine-grained scores; if False, groups into intervals
        switch_to_key: If True, sorts by difficulty keys; if False, sorts by frequency
    """
    # Initialize storage for raw and sorted distributions
    dict_sum = {}  # Raw distributions per file
    dict_sum_sorted = {}  # Sorted/processed distributions per file
    
    # Process each JSONL file
    for dir_add, _, file_list in os.walk(data_path):
        for file in file_list:
            if not file.endswith('.jsonl'):
                continue
                
            print(f"Processing {file}")
            input_file = os.path.join(dir_add, file)
            
            with open(input_file, "r", encoding="utf-8") as f:
                dict_single = {}  # Difficulty distribution for this file
                lines = f.readlines()
                len_min_max, cond_min_max, sym_min_max = min_max_score(lines)
                
                # Count occurrences of each difficulty score
                for line in lines:
                    data = json.loads(line)
                    difficulty_score = norm_num(data, len_min_max, cond_min_max, sym_min_max)
                    key = str(difficulty_score)
                    dict_single[key] = dict_single.get(key, 0) + 1
                
            # Sort and process the distribution
            sorted_dict_single = sort_dict_by_key(dict_single, granularity=granularity, switch_to_key_value=switch_to_key)
            dict_sum[file] = dict_single
            dict_sum_sorted[file] = sorted_dict_single
    
    # Calculate aggregate statistics across all files
    all_sum = {}
    for key, sub_dict in dict_sum.items():
        if key != "all":  # Skip the "all" key if it already exists
            for k, v in sub_dict.items():
                all_sum[k] = all_sum.get(k, 0) + v
    dict_sum["all"] = all_sum
    dict_sum_sorted["all"] = sort_dict_by_key(all_sum, granularity=granularity, switch_to_key_value=switch_to_key)
    
    # Ensure output directory exists and write results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dict_sum_sorted, f, ensure_ascii=False, indent=4)

def main():
    """Main entry point for the difficulty calculation tool."""
    parser = argparse.ArgumentParser(description='Process JSONL files to generate difficulty scores or distribution statistics')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Difficulty score generation subcommand
    difficulty_parser = subparsers.add_parser('difficulty', help='Generate difficulty scores for all records')
    difficulty_parser.add_argument('-i', '--input', required=True, help='Input data directory containing JSONL files')
    difficulty_parser.add_argument('-o', '--output', required=True, help='Output directory for enhanced JSONL files')
    
    # Distribution analysis subcommand
    distribution_parser = subparsers.add_parser('distribution', help='Generate difficulty distribution statistics')
    distribution_parser.add_argument('-i', '--input', required=True, help='Input data directory containing JSONL files')
    distribution_parser.add_argument('-o', '--output', required=True, help='Output JSON file path for distribution data')
    distribution_parser.add_argument('--granularity', action='store_true', help='Maintain fine-grained scores (do not merge into intervals)')
    distribution_parser.add_argument('--sort-by-key', action='store_true', help='Sort by difficulty keys (default: sort by frequency)')
    
    args = parser.parse_args()
    
    if args.command == 'difficulty':
        print("Starting difficulty score generation...")
        generate_difficulty(args.input, args.output)
        print("Difficulty score generation completed!")
    elif args.command == 'distribution':
        print("Starting difficulty distribution analysis...")
        generate_distribution(
            args.input, 
            args.output, 
            granularity=args.granularity, 
            switch_to_key=args.sort_by_key
        )
        print("Difficulty distribution analysis completed!")

if __name__ == "__main__":
    main()