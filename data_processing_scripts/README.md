# Data Processing Scripts for PuzzleClone

This directory contains a comprehensive set of Python scripts and tools for processing puzzle data into standardized benchmark format. The scripts handle difficulty calculation, duplicate detection and removal, and dataset splitting for machine learning workflows.

## 🚀 Quick Start

For a streamlined processing workflow, use the main transformation script:

```bash
# Process from raw data (most common case - complete pipeline)
./transform_data.sh -i /path/to/raw/data --dsl-dir /path/to/dsl -o /path/to/output -r /path/to/reports

# Process from already formatted data (skips formatting)
./transform_data.sh --formatted-input /path/to/formatted/data -o /path/to/output -r /path/to/reports

# Skip specific steps
./transform_data.sh -i /path/to/raw/data -o /path/to/output -r /path/to/reports --skip-difficulty --skip-duplicate

# View all options
./transform_data.sh --help
```

**Required Parameters:**
- Output directory (`-o/--output`): Where processed data will be stored
- Reports directory (`-r/--reports`): Where analysis reports will be stored  
- Input source: Either `-i/--input` (for raw data) OR `--formatted-input` (for already formatted data)

## 📁 Directory Structure

```
data_processing_scripts/
├── README.md                 # This documentation
├── transform_data.sh         # Main transformation pipeline (recommended)
├── run.sh                    # Legacy batch script (deprecated)
├── data_format.py           # Data formatting and metadata addition
├── cal_difficulty.py         # Difficulty score calculation
├── check_duplicate.py        # Duplicate configuration detection
├── deduplicate.py           # Duplicate removal
├── split_rl.py              # Dataset splitting for ML
└── gen_sft_data.py  # SFT data sampling
```

## 🔧 Individual Scripts

### 1. Data Formatting (`data_format.py`)

Formats raw puzzle data by adding metadata fields and calculating variable scaling parameters.

**Features:**
- Adds question type (qtype) and evaluation type (eval_type) metadata
- Calculates normalized variable scale (vars_scale) from DSL specifications  
- Adds unique identifiers if requested
- Adds source field based on filename
- Handles interactive metadata input for new files

**Usage:**

```bash
# Basic formatting with metadata
python data_format.py -i raw_data_dir -o formatted_data_dir

# Include DSL-based variable scaling
python data_format.py -i raw_data_dir -o formatted_data_dir -d dsl_specs_dir

# Add unique IDs to records
python data_format.py -i raw_data_dir -o formatted_data_dir --add-ids

# Complete formatting with all features
python data_format.py -i raw_data_dir -o formatted_data_dir -d dsl_specs_dir --add-ids
```

**DSL Integration:**
If a DSL directory is provided, the script:
- Reads corresponding JSON files for variable domain specifications
- Calculates min/max ranges for each variable across all records
- Normalizes variables based on their difficulty factors
- Computes average normalized scale as `vars_scale` parameter

**Output Format:**
Each record gets enhanced with:
- `qtype`: Question type classification
- `eval_type`: Evaluation method specification  
- `source`: Source category (from filename)
- `id`: Unique identifier (if --add-ids used)
- `parameters.vars_scale`: A scale measuring the quantitative difficulty of the puzzle

### 2. Difficulty Calculation (`cal_difficulty.py`)

Calculates normalized difficulty scores for puzzle problems based on multiple metrics.

**Features:**
- Analyzes problem text length, condition count, symbol count, and variable scale
- Normalizes scores to [0,1] range using min-max normalization
- Generates difficulty distribution statistics

**Usage:**

```bash
# Add difficulty scores to all JSONL files
python cal_difficulty.py difficulty -i input_dir -o output_dir

# Generate difficulty distribution analysis
python cal_difficulty.py distribution -i input_dir -o output_file.json

# Fine-grained distribution (preserve individual scores)
python cal_difficulty.py distribution -i input_dir -o output.json --granularity

# Sort by difficulty values instead of frequency
python cal_difficulty.py distribution -i input_dir -o output.json --sort-by-key
```

**Output Format:**
Each record gets a new `difficulty` field with a score between 0 and 1.

### 2. Duplicate Detection (`check_duplicate.py`)

Identifies problems with equivalent numeric configurations using sophisticated signature matching.

**Features:**
- Extracts numeric signatures from nested configuration data
- Handles special numeric patterns (`__123__`, `__45.67__`)
- Supports both detailed and summary reporting

**Usage:**

```bash
# Generate detailed duplicate report
python check_duplicate.py detail -i input_dir -o duplicate_report.txt

# Generate CSV summary
python check_duplicate.py overview -i input_dir -o duplicate_summary.csv

# Print to console (no output file)
python check_duplicate.py detail -i input_dir
```

### 3. Deduplication (`deduplicate.py`)

Removes duplicate problems based on numeric configuration signatures.

**Features:**
- Preserves the first occurrence of each unique configuration
- Maintains original data structure and formatting
- Provides processing statistics

**Usage:**

```bash
# Remove duplicates from directory of JSONL files
python deduplicate.py -i input_dir -o output_dir

# Custom paths
python deduplicate.py -i /path/to/data -o /path/to/clean_data
```

### 4. Dataset Splitting (`split_rl.py`)

Splits data into training, validation, and test sets with difficulty-based stratification.

**Features:**
- Separates problems into "normal" and "hard" difficulty categories
- Creates balanced train/validate/test splits
- Generates both regular and RL-specific training sets
- Maintains category distribution across splits

**Usage:**

```bash
# Basic splitting with default parameters
python split_rl.py -i input_dir -o output_dir

# Custom random seed for reproducibility
python split_rl.py -i input_dir -o output_dir --seed 123
```

**Output Structure:**
```
output_dir/
├── normal/
│   ├── SFT.jsonl         # SFT training set (supervised fine-tuning)
│   ├── RL_train.jsonl    # RL training subset
│   ├── RL_validate.jsonl # RL validation set
│   └── Test.jsonl        # Test set
└── hard/
    ├── SFT.jsonl         # SFT training set (supervised fine-tuning)
    ├── RL_train.jsonl    # RL training subset
    ├── RL_validate.jsonl # RL validation set
    └── Test.jsonl        # Test set
```

### 5. SFT Data Sampling (`gen_sft_data.py`)

Extracts balanced samples from training sets for supervised fine-tuning or other ML tasks.

**Features:**
- Samples from both normal and hard difficulty categories
- Maintains category balance in selected data
- Provides detailed sampling statistics
- Supports different input file types (SFT.jsonl, RL_train.jsonl, etc.)

**Usage:**

```bash
# Extract 50 problems per category from SFT.jsonl files (default)
python gen_sft_data.py --base_dir splitted_data --output_dir sft_data

# Custom sample size and seed
python gen_sft_data.py --base_dir splitted_data --output_dir sft_data --total 100 --seed 42

# Use RL training data instead of SFT data
python gen_sft_data.py --base_dir splitted_data --output_dir rl_samples --input_file RL_train.jsonl
```

## 🔄 Complete Pipeline Workflow

The recommended workflow processes data through the following stages:

### Using the Automated Pipeline (Recommended)
```bash
# Complete pipeline from raw data
./transform_data.sh --raw-input raw_data --dsl-dir dsl_specs -o output_dir -r reports_dir --add-ids

# Pipeline from formatted data (skipping format step)
./transform_data.sh -i formatted_data -o output_dir -r reports_dir
```

### Manual Step-by-Step Processing

### Stage 1: Data Formatting
```bash
python data_format.py -i raw_data -o formatted_data -d dsl_specs --add-ids
```
- Input: Raw JSONL files with basic puzzle data
- Adds metadata fields (qtype, eval_type, source)
- Calculates variable scaling parameters from DSL specifications
- Adds unique identifiers for tracking

### Stage 2: Difficulty Analysis
```bash
python cal_difficulty.py difficulty -i formatted_data -o data_with_difficulty
```
- Calculates normalized difficulty scores
- Adds `difficulty` field to each record

### Stage 3: Duplicate Detection and Removal
```bash
python check_duplicate.py overview -i data_with_difficulty -o duplicate_report.csv
python deduplicate.py -i data_with_difficulty -o deduplicated_data
```
- Identifies and removes configuration duplicates
- Preserves data quality and uniqueness

### Stage 4: Dataset Splitting
```bash
python split_rl.py -i deduplicated_data -o final_dataset
```
- Creates train/validate/test splits
- Separates by difficulty level
- Prepares data for ML training

### Stage 5: SFT Sample Generation (Optional)
```bash
python gen_sft_data.py --base_dir final_dataset --output_dir sft_samples
```
- Extracts balanced samples for fine-tuning
- Maintains category representation

## 📊 Data Format Requirements

### Raw Input Format
JSONL files where each line contains basic puzzle data:
```json
{
  "problem": "Problem statement text",
  "answer": "Expected answer",
  "config": {
    "numeric_field1": 123,
    "nested_config": {
      "field2": [1, 2, 3],
      "field3": "__456__"
    }
  },
  "parameters": {
    "cond_num": 5,
    "sym_num": 3
  }
}
```

### Formatted Output
After data formatting, records include:
```json
{
  "problem": "Problem statement text",
  "answer": "Expected answer", 
  "config": { ... },
  "parameters": {
    "cond_num": 5,
    "sym_num": 3,
    "vars_scale": 0.7
  },
  "qtype": "简答题",
  "eval_type": "nominal",
  "source": "category_name",
  "id": "category_name-0001"
}
```

### Final Processing Enhancements
After complete processing, records include:
- `difficulty`: Normalized difficulty score (0-1)
- `qtype`: Question type classification
- `eval_type`: Evaluation method specification
- `source`: Source category identifier
- `id`: Unique record identifier
- `parameters.vars_scale`: Variable difficulty scaling factor
- Preserved original fields and structure

## 🛠️ Configuration Options

### Difficulty Calculation
- **Metrics**: Problem length, condition count, symbol count, variable scale
- **Normalization**: Min-max scaling within each file
- **Distribution**: Configurable granularity and sorting

### Deduplication
- **Signature**: Based on numeric configuration values
- **Special Patterns**: Handles `__number__` encoded values
- **Pool Sorting**: Order-independent comparison for array fields

### Dataset Splitting
- **Difficulty Threshold**: 0.5 (configurable)
- **Train Ratio**: 80% (configurable)
- **Validation Ratio**: 10% (configurable)
- **Test Ratio**: 10% (remainder)

## 🚨 Error Handling

All scripts include comprehensive error handling:
- **Invalid JSON**: Malformed lines are skipped with warnings
- **Missing Files**: Clear error messages for missing inputs
- **Empty Datasets**: Graceful handling of empty or invalid data
- **Directory Creation**: Automatic creation of output directories

## 📈 Performance Considerations

- **Memory Usage**: Streams large files for efficient processing
- **Reproducibility**: Consistent random seeds across runs
- **Parallelization**: Scripts can be run on different file subsets
- **Progress Tracking**: Verbose output for long-running operations

## 🤝 Integration with External Tools

These scripts are designed to integrate with:
- **Machine Learning Pipelines**: Standard train/validate/test format
- **Data Analysis Tools**: JSON and CSV output formats
- **Version Control**: Deterministic outputs with fixed seeds
- **Batch Processing**: Shell script automation support

## 📚 Additional Resources

For more advanced usage and customization:
1. Review the source code comments for implementation details
2. Use `--help` flag with any script for detailed options
3. Check the main transformation script for pipeline examples
4. Refer to individual script docstrings for function specifications

---

*This documentation covers the complete data processing workflow for the Puzzle Clone dataset. For questions or contributions, please refer to the project repository.*