import os
import json
import random
import argparse
from collections import defaultdict

def extract_data(base_dir, output_dir, total_num=50, seed=42, input_file='SFT.jsonl'):
    """
    Extract balanced sample data from normal and hard training sets.
    
    This function samples problems from both normal and hard difficulty categories,
    ensuring balanced representation across different puzzle types. It reads from
    the specified input files in the data splitting pipeline output.
    
    Args:
        base_dir: Base directory containing 'normal' and 'hard' subdirectories with training files
        output_dir: Output directory for sampled training data
        total_num: Total number of problems to sample per category
        seed: Random seed for reproducible sampling
        input_file: Name of the input file to read from (default: 'SFT.jsonl')
    """
    # Set random seed for reproducible results
    random.seed(seed)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define training set file paths (using specified input files from split_rl.py output)
    normal_train_path = os.path.join(base_dir, 'normal', input_file)
    hard_train_path = os.path.join(base_dir, 'hard', input_file)
    
    # Initialize data structure: organize problems by category and difficulty
    # Structure: {category: {'normal': [problem_list], 'hard': [problem_list]}}
    category_data = defaultdict(lambda: {'normal': [], 'hard': []})
    
    # Read normal training set data
    if os.path.exists(normal_train_path):
        with open(normal_train_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if 'source' in item:
                        category = item['source']
                        category_data[category]['normal'].append(item)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line (normal/{input_file})")
    else:
        print(f"Error: Cannot find file {normal_train_path}")
        return
    
    # Read hard training set data
    if os.path.exists(hard_train_path):
        with open(hard_train_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if 'source' in item:
                        category = item['source']
                        category_data[category]['hard'].append(item)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line (hard/{input_file})")
    else:
        print(f"Error: Cannot find file {hard_train_path}")
        return
    
    # Prepare output data structures
    selected_data_normal = []  # Selected normal difficulty problems
    selected_data_hard = []    # Selected hard difficulty problems
    stats = defaultdict(int)   # Statistics for reporting
    
    # Process data for each category
    for category, data in category_data.items():
        # Get problem lists for current category
        normal_list = data['normal']
        hard_list = data['hard']
        
        # Randomly shuffle problem order for fair sampling
        random.shuffle(normal_list)
        random.shuffle(hard_list)
        
        # Determine number of hard problems to sample (up to half of total)
        hard_count = min(total_num//2, len(hard_list))
        
        # Determine number of normal problems to sample (remaining quota)
        normal_count = min(total_num - hard_count, len(normal_list))
        
        # Record statistics for this category
        stats[category] = {
            'normal': len(normal_list),
            'hard': len(hard_list),
            'selected_normal': normal_count,
            'selected_hard': hard_count
        }
        
        # Sample problems from each difficulty level
        if hard_count > 0:
            selected_data_hard.extend(hard_list[:hard_count])
        if normal_count > 0:
            selected_data_normal.extend(normal_list[:normal_count])
    
    # Randomly shuffle final selected problems
    random.shuffle(selected_data_normal)
    random.shuffle(selected_data_hard)
    
    # Output statistics
    print("==== Category Statistics ====")
    print(f"Total categories: {len(category_data)}")
    print(f"Selected total problems (normal): {len(selected_data_normal)}")
    print(f"Selected total problems (hard): {len(selected_data_hard)}")
    print("Category, Original Normal, Original Hard, Selected Normal, Selected Hard")
    for category, data in category_data.items():
        normal_list = stats[category]["normal"]
        hard_list = stats[category]["hard"]
        normal_count = stats[category]["selected_normal"]
        hard_count = stats[category]["selected_hard"]
        print(category, normal_list, hard_list, normal_count, hard_count)
    print("Total normal selected: " + str(sum([stats[category]["selected_normal"] for category, data in category_data.items()])))
    print("Total hard selected: " + str(sum([stats[category]["selected_hard"] for category, data in category_data.items()])))
    
    # Save selected problems to output files
    normal_output_path = os.path.join(output_dir, 'train_normal.jsonl')
    with open(normal_output_path, 'w', encoding='utf-8') as f:
        for item in selected_data_normal:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    hard_output_path = os.path.join(output_dir, 'train_hard.jsonl')
    with open(hard_output_path, 'w', encoding='utf-8') as f:
        for item in selected_data_hard:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\nSelected problems saved to: {output_dir}")
    print(f"Random seed used: {seed}")
    print(f"Total problems selected: {len(selected_data_normal) + len(selected_data_hard)}")

if __name__ == "__main__":
    """Main entry point for the SFT data extraction tool."""
    parser = argparse.ArgumentParser(description='Extract balanced sample data from normal and hard training sets by category')
    parser.add_argument('--base_dir', required=True, help='Base directory containing normal and hard subdirectories with training files')
    parser.add_argument('--output_dir', default='selected_data', help='Output directory path')
    parser.add_argument('--total', type=int, default=50, help='Total number of problems to select per category')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible results')
    parser.add_argument('--input_file', default='SFT.jsonl', help='Input file name to read from (default: SFT.jsonl, alternatives: RL_train.jsonl, RL_validate.jsonl, Test.jsonl)')
    
    args = parser.parse_args()
    
    extract_data(args.base_dir, args.output_dir, total_num=args.total, seed=args.seed, input_file=args.input_file)