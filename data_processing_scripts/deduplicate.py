import json
import os
import re
import argparse
from typing import Dict, Any, Tuple, List, Union

def to_hashable(obj: Any, key_name: str = None) -> Any:
    """
    Convert data structures to hashable types for deduplication.
    
    This function transforms complex data structures into hashable tuples
    while preserving semantic equivalence. Special handling is applied
    for "pool" arrays to ensure order-independent comparison.
    
    Args:
        obj: The object to convert (dict, list, tuple, or primitive type)
        key_name: Name of the current key being processed (used for special handling)
        
    Returns:
        Hashable representation of the input object
    """
    if isinstance(obj, dict):
        # Process nested dictionaries recursively, passing current key name
        return tuple(sorted((k, to_hashable(v, key_name=k)) for k, v in obj.items()))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        # Handle nested arrays: sort outer layer only for "pool" keys with nested arrays
        processed_items = []
        for item in obj:
            if isinstance(item, (list, tuple)):
                processed_items.append(tuple(to_hashable(subitem, key_name=None) for subitem in item))
            else:
                processed_items.append(to_hashable(item, key_name=None))
        
        # Sort outer layer only for "pool" keys containing nested arrays
        if key_name == "pool" and any(isinstance(item, tuple) for item in processed_items):
            return tuple(sorted(processed_items))
        else:
            return tuple(processed_items)
    elif isinstance(obj, str) and re.match(r"^__(\d+)__$", obj):
        # Handle special numeric pattern "__x__"
        return int(re.match(r"^__(\d+)__$", obj).group(1))
    elif isinstance(obj, str) and re.match(r"^__(\d+\.\d+)__$", obj):
        # Handle special float pattern "__x.y__"
        return float(re.match(r"^__(\d+\.\d+)__$", obj).group(1))
    else:
        # Return primitive types as-is
        return obj

def is_numeric_value(value: Any) -> bool:
    """
    Check if a value represents numeric data, including special patterns.
    
    This function identifies values that should be considered for duplicate
    detection based on their numeric content.
    
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
    all values that represent numeric data for deduplication comparison.
    
    Args:
        config: Configuration dictionary to process
        prefix: Current key path prefix for nested traversal
        
    Returns:
        List of (key_path, hashable_value) tuples for all numeric values
    """
    numeric_items = []
    
    for key, value in config.items():
        if key == '_query':
            continue  # Skip query fields as they're not part of core configuration
        
        # Create full key path with prefix
        full_key = f"{prefix}.{key}" if prefix else key
        
        # Check if value is numeric
        if is_numeric_value(value):
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                numeric_items.extend(extract_numeric_values(value, full_key))
            else:
                # Normalize numeric values for comparison (pass key name for special handling)
                hashable_value = to_hashable(value, key_name=key)
                numeric_items.append((full_key, hashable_value))
    
    return numeric_items

def get_numeric_signature(config: Dict[str, Any]) -> Tuple[Tuple[str, Any]]:
    """
    Extract numeric feature signature from configuration data.
    
    This function creates a unique signature for each configuration by
    extracting and sorting all numeric values. Records with identical
    signatures are considered duplicates.
    
    Args:
        config: Configuration dictionary from a data record
        
    Returns:
        Tuple of sorted (key_path, value) pairs representing the numeric signature
    """
    # Extract all numeric key-value pairs recursively
    numeric_items = extract_numeric_values(config)
    
    # Sort by key path to ensure consistent ordering
    numeric_items.sort(key=lambda x: x[0])
    
    return tuple(numeric_items)

def deduplicate_jsonl_file(input_path: str, output_path: str) -> None:
    """
    Remove duplicates from a single JSONL file and write results to output file.
    
    This function processes a JSONL file, identifies records with duplicate
    numeric configurations, and writes only unique records to the output file.
    
    Args:
        input_path: Path to the input JSONL file
        output_path: Path to the output JSONL file for unique records
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        signatures_seen = set()  # Track seen numeric signatures
        unique_records = []      # Store unique records
        
        # Process each line in the file
        for line in infile:
            try:
                record = json.loads(line)
                config = record.get("config", {})
                
                # Generate numeric signature for duplicate detection
                signature = get_numeric_signature(config)
                
                # Keep record if it has no numeric config or signature is new
                if not signature or signature not in signatures_seen:
                    unique_records.append(line)
                    if signature:
                        signatures_seen.add(signature)
                    
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                continue
        
        # Write deduplicated records to output file
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.writelines(unique_records)

def process_jsonl_files(input_dir: str, output_dir: str) -> None:
    """
    Process all JSONL files in input directory and write deduplicated results to output directory.
    
    This function processes each JSONL file in the input directory, removes
    duplicates based on numeric configuration signatures, and saves the
    cleaned data to corresponding files in the output directory.
    
    Args:
        input_dir: Input directory containing JSONL files
        output_dir: Output directory for deduplicated JSONL files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all JSONL files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            print(f"Processing file: {filename}")
            deduplicate_jsonl_file(input_path, output_path)
            print(f"Saved deduplicated results to: {output_path}")

if __name__ == "__main__":
    """Main entry point for the deduplication tool."""
    parser = argparse.ArgumentParser(description='Remove duplicates from JSONL files based on numeric configuration signatures')
    parser.add_argument('-i', '--input', default='puzzle_clone_public/data', 
                       help='Input directory path (default: "puzzle_clone_public/data")')
    parser.add_argument('-o', '--output', default='puzzle_clone_public/deduplicated_data', 
                       help='Output directory path (default: "puzzle_clone_public/deduplicated_data")')
    
    args = parser.parse_args()
    
    print("Starting file deduplication...")
    process_jsonl_files(args.input, args.output)
    print("Deduplication completed!")