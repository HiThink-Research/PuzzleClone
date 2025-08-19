import os
import json
import random
from pathlib import Path
from collections import defaultdict

def split_dataset(input_dir, output_dir, difficulty_threshold=0.5, train_percentage=0.8, validate_percentage=0.1, seed=42):
    """
    Split puzzle dataset into train/validate/test sets by difficulty and source type.
    
    This function processes JSONL files containing puzzle data, splits them based on
    difficulty scores, and creates balanced train/validate/test splits for both
    normal and hard difficulty levels.
    
    Args:
        input_dir: Input directory containing JSONL files
        output_dir: Output directory for split datasets
        difficulty_threshold: Threshold for normal/hard classification (default: 0.5)
        train_percentage: Percentage of data for training (default: 0.8)
        validate_percentage: Percentage of data for validation (default: 0.1)
        seed: Random seed for reproducible splits (default: 42)
    """
    # Set random seed for reproducible results
    random.seed(seed)
    
    # Initialize data storage structure
    # Structure: source_type -> difficulty_level -> [items]
    source_data = defaultdict(lambda: defaultdict(list))
    
    # Process all JSONL files in the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.jsonl'):
            file_path = os.path.join(input_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        difficulty = item.get('difficulty', 0)
                        source_type = item.get('source', "default")
                        
                        # Classify by difficulty level
                        difficulty_level = 'hard' if difficulty > difficulty_threshold else 'normal'
                        source_data[source_type][difficulty_level].append(item)
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping invalid JSON line (file: {file_name})")
    
    # Create output directory structure
    output_paths = {
        'normal': {
            'train': os.path.join(output_dir, 'normal', 'SFT.jsonl'),
            'train_rl': os.path.join(output_dir, 'normal', 'RL_train.jsonl'),
            'validate': os.path.join(output_dir, 'normal', 'RL_validate.jsonl'),
            'test': os.path.join(output_dir, 'normal', 'Test.jsonl')
        },
        'hard': {
            'train': os.path.join(output_dir, 'hard', 'SFT.jsonl'),
            'train_rl': os.path.join(output_dir, 'hard', 'RL_train.jsonl'),
            'validate': os.path.join(output_dir, 'hard', 'RL_validate.jsonl'),
            'test': os.path.join(output_dir, 'hard', 'Test.jsonl')
        }
    }
    
    # Ensure output directories exist
    for category in ['normal', 'hard']:
        Path(output_paths[category]['train']).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize final merged datasets
    merged_data = {
        'normal': defaultdict(list),
        'hard': defaultdict(list)
    }
    
    # Process each source type and difficulty combination
    for source_type, difficulty_groups in source_data.items():
        for difficulty_level, items in difficulty_groups.items():
            if not items:
                continue
                
            # Randomly shuffle current group data
            random.shuffle(items)
            
            # Calculate split points
            validate_index = int((train_percentage + validate_percentage) * len(items))
            train_rl_index = validate_index - 5  # Reserve 5 items for validation from training portion
            
            # Create subsets
            train_rl_items = items[:train_rl_index]     # RL training subset
            validate_items = items[train_rl_index:validate_index]  # Validation subset
            train_items = items[:validate_index]        # Full training portion (includes RL training and validation)
            test_items = items[validate_index:]         # Test subset
            
            # Add to merged datasets
            merged_data[difficulty_level]['train_rl'].extend(train_rl_items)
            merged_data[difficulty_level]['train'].extend(train_items)
            merged_data[difficulty_level]['validate'].extend(validate_items)
            merged_data[difficulty_level]['test'].extend(test_items)
    
    # Write final merged files
    for difficulty_level, data_groups in merged_data.items():
        # Write training set
        with open(output_paths[difficulty_level]['train'], 'w', encoding='utf-8') as f:
            for item in data_groups['train']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # Write reinforcement learning training set
        with open(output_paths[difficulty_level]['train_rl'], 'w', encoding='utf-8') as f:
            for item in data_groups['train_rl']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # Write validation set
        with open(output_paths[difficulty_level]['validate'], 'w', encoding='utf-8') as f:
            for item in data_groups['validate']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # Write test set
        with open(output_paths[difficulty_level]['test'], 'w', encoding='utf-8') as f:
            for item in data_groups['test']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Processing completed! Results saved in: {output_dir}")

if __name__ == "__main__":
    """Main entry point for the dataset splitting tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Split dataset by problem type and difficulty level')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input JSONL files directory')
    parser.add_argument('-o', '--output', type=str, default='output', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, required=False, help='Random seed for reproducible results')
    
    args = parser.parse_args()
    
    split_dataset(args.input, args.output, seed=args.seed)