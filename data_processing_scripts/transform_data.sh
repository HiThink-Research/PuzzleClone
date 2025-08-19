#!/bin/bash

# Data Transformation Pipeline for Puzzle Clone Dataset
# This script provides a streamlined workflow for transforming puzzle data
# into the standard benchmark format with difficulty analysis and deduplication.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Data Transformation Pipeline for Puzzle Clone Dataset"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Basic Usage:"
    echo "  # Process from raw data (most common case)"
    echo "  $0 -i /path/to/raw/data --dsl-dir /path/to/dsl -o /path/to/output [-r /path/to/reports]"
    echo ""
    echo "  # Process from already formatted data (skip formatting)"
    echo "  $0 --formatted-input /path/to/formatted/data -o /path/to/output [-r /path/to/reports]"
    echo ""
    echo "Options:"
    echo "  -i, --input DIR      Raw input data directory (required for most use cases)"
    echo "  --dsl-dir DIR        DSL specification directory (optional, used with -i/--input)"
    echo "  --formatted-input DIR Formatted input data directory (use when skipping formatting)"
    echo "  -o, --output DIR     Output base directory (required)"
    echo "  -r, --reports DIR    Reports output directory (optional, if not specified, reports are skipped)"
    echo "  --skip-format        Explicitly skip data formatting step"
    echo "  --skip-difficulty    Skip difficulty calculation step"
    echo "  --skip-duplicate     Skip duplicate checking and removal"
    echo "  --skip-split         Skip data splitting step"
    echo "  --add-ids            Add unique IDs during formatting"
    echo "  --keep-reports       Keep intermediate report files"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Required Parameters:"
    echo "  - Output directory (-o/--output): Where processed data will be stored"
    echo "  - Input source: Either -i/--input (for raw data) OR --formatted-input (for already formatted data)"
    echo ""
    echo "Optional Parameters:"
    echo "  - Reports directory (-r/--reports): Where analysis reports will be stored (if not specified, reports are skipped)"
    echo ""
    echo "Pipeline Steps:"
    echo "  1. Format raw data with metadata and variable scaling (skipped if using --formatted-input)"
    echo "  2. Calculate difficulty scores for all problems"
    echo "  3. Check for duplicate configurations and remove duplicates"
    echo "  4. Split data into train/validate/test sets"
    echo ""
    echo "Usage Modes:"
    echo "  1. Full Pipeline: Use -i/--input to process from raw data through all steps"
    echo "  2. Partial Pipeline: Use --formatted-input to start from already formatted data"
    echo "  3. Custom Pipeline: Use --skip-* flags to skip specific processing steps"
    echo ""
    echo "Output Structure:"
    echo "  \$OUTPUT_DIR/"
    echo "  ├── 1_data_formatted/        # Formatted data with metadata"
    echo "  ├── 2_data_with_difficulty/  # Data with difficulty scores"
    echo "  ├── 3_deduplicated_data/     # Deduplicated data"
    echo "  └── 4_splitted/              # Train/validate/test splits"
    echo "      ├── normal/"
    echo "      └── hard/"
    echo ""
    echo "Reports Structure:"
    echo "  \$REPORTS_DIR/"
    echo "  ├── difficulty_distribution/"
    echo "  └── check_duplicate/"
}

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# Check if required Python scripts exist
check_dependencies() {
    local script_dir="$(dirname "$0")"
    local required_scripts=("data_format.py" "cal_difficulty.py" "check_duplicate.py" "deduplicate.py" "split_rl.py")
    
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$script_dir/$script" ]]; then
            log_error "Required script not found: $script"
            echo "Please ensure all Python scripts are in the same directory as this script."
            exit 1
        fi
    done
    log_success "All required Python scripts found"
}

# Create directory if it doesn't exist
ensure_dir() {
    if [[ ! -d "$1" ]]; then
        mkdir -p "$1"
        log "Created directory: $1"
    fi
}

# Parse command line arguments
parse_args() {
    RAW_INPUT_DIR=""
    DSL_DIR=""
    FORMATTED_INPUT_DIR=""
    OUTPUT_DIR=""
    REPORTS_DIR=""
    SKIP_FORMAT=false
    SKIP_DIFFICULTY=false
    SKIP_DUPLICATE=false
    SKIP_SPLIT=false
    ADD_IDS=false
    KEEP_REPORTS=false
    USER_PROVIDED_FORMATTED=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                RAW_INPUT_DIR="$2"
                shift 2
                ;;
            --dsl-dir)
                DSL_DIR="$2"
                shift 2
                ;;
            --formatted-input)
                FORMATTED_INPUT_DIR="$2"
                USER_PROVIDED_FORMATTED=true
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -r|--reports)
                REPORTS_DIR="$2"
                shift 2
                ;;
            --skip-format)
                SKIP_FORMAT=true
                shift
                ;;
            --skip-difficulty)
                SKIP_DIFFICULTY=true
                shift
                ;;
            --skip-duplicate)
                SKIP_DUPLICATE=true
                shift
                ;;
            --skip-split)
                SKIP_SPLIT=true
                shift
                ;;
            --add-ids)
                ADD_IDS=true
                shift
                ;;
            --keep-reports)
                KEEP_REPORTS=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Auto-skip formatting if user provided formatted input directory
    if [[ "$USER_PROVIDED_FORMATTED" == true && "$SKIP_FORMAT" == false ]]; then
        SKIP_FORMAT=true
        log "Auto-skipping format step since formatted input directory was provided"
    fi
    
    # Validate required parameters
    if [[ -z "$OUTPUT_DIR" ]]; then
        log_error "Output directory is required. Use -o or --output to specify."
        show_help
        exit 1
    fi
    
    # Validate input paths based on mode
    if [[ "$SKIP_FORMAT" == false ]]; then
        if [[ -z "$RAW_INPUT_DIR" ]]; then
            log_error "Raw input directory is required when not skipping format. Use -i or --input to specify."
            show_help
            exit 1
        fi
        # Set default INPUT_DIR for formatted data if not provided
        if [[ -z "$FORMATTED_INPUT_DIR" ]]; then
            INPUT_DIR="$OUTPUT_DIR/1_data_formatted"
        else
            INPUT_DIR="$FORMATTED_INPUT_DIR"
        fi
    else
        if [[ -z "$FORMATTED_INPUT_DIR" ]]; then
            log_error "Formatted input directory is required when skipping format. Use --formatted-input to specify."
            show_help
            exit 1
        fi
        INPUT_DIR="$FORMATTED_INPUT_DIR"
    fi
}

# Validate input directories
validate_input() {
    # Validate based on whether we're skipping format step
    if [[ "$SKIP_FORMAT" == false ]]; then
        # Check raw input directory
        if [[ ! -d "$RAW_INPUT_DIR" ]]; then
            log_error "Raw input directory does not exist: $RAW_INPUT_DIR"
            exit 1
        fi
        
        # Check if there are any .jsonl files in raw input
        if ! ls "$RAW_INPUT_DIR"/*.jsonl 1> /dev/null 2>&1; then
            log_error "No .jsonl files found in raw input directory: $RAW_INPUT_DIR"
            exit 1
        fi
        
        log_success "Raw input directory validated: $RAW_INPUT_DIR"
        
        # Check DSL directory if provided
        if [[ -n "$DSL_DIR" && ! -d "$DSL_DIR" ]]; then
            log_warning "DSL directory does not exist: $DSL_DIR (vars_scale calculation will be skipped)"
            DSL_DIR=""
        fi
    else
        # Check formatted input directory
        if [[ ! -d "$INPUT_DIR" ]]; then
            log_error "Formatted input directory does not exist: $INPUT_DIR"
            exit 1
        fi
        
        # Check if there are any .jsonl files
        if ! ls "$INPUT_DIR"/*.jsonl 1> /dev/null 2>&1; then
            log_error "No .jsonl files found in formatted input directory: $INPUT_DIR"
            exit 1
        fi
        
        log_success "Formatted input directory validated: $INPUT_DIR"
    fi
}

# Main transformation pipeline
run_pipeline() {
    local script_dir="$(dirname "$0")"
    
    log "Starting data transformation pipeline..."
    if [[ "$SKIP_FORMAT" == false ]]; then
        log "Raw input directory: $RAW_INPUT_DIR"
        log "DSL directory: $DSL_DIR"
    fi
    log "Working input directory: $INPUT_DIR"
    log "Output directory: $OUTPUT_DIR"
    if [[ -n "$REPORTS_DIR" ]]; then
        log "Reports directory: $REPORTS_DIR"
    else
        log "Reports directory: Not specified (reports will be skipped)"
    fi
    
    # Create output directories
    ensure_dir "$OUTPUT_DIR"
    if [[ -n "$REPORTS_DIR" ]]; then
        ensure_dir "$REPORTS_DIR"
    fi
    
    # Step 1: Format raw data (optional)
    if [[ "$SKIP_FORMAT" == false ]]; then
        log "Step 1: Formatting raw data with metadata and variable scaling..."
        ensure_dir "$INPUT_DIR"
        
        # Build formatting command
        format_cmd="python \"$script_dir/data_format.py\" -i \"$RAW_INPUT_DIR\" -o \"$INPUT_DIR\""
        if [[ -n "$DSL_DIR" ]]; then
            format_cmd="$format_cmd -d \"$DSL_DIR\""
        fi
        if [[ "$ADD_IDS" == true ]]; then
            format_cmd="$format_cmd --add-ids"
        fi
        
        eval $format_cmd
        log_success "Data formatting completed"
        
        INPUT_FOR_NEXT_STEP="$INPUT_DIR"
    else
        log_warning "Skipping data formatting step"
        INPUT_FOR_NEXT_STEP="$INPUT_DIR"
    fi
    
    # Step 2: Calculate difficulty scores
    if [[ "$SKIP_DIFFICULTY" == false ]]; then
        log "Step 2: Calculating difficulty scores..."
        local difficulty_output="$OUTPUT_DIR/2_data_with_difficulty"
        ensure_dir "$difficulty_output"
        
        python "$script_dir/cal_difficulty.py" difficulty -i "$INPUT_FOR_NEXT_STEP" -o "$difficulty_output"
        log_success "Difficulty calculation completed"
        
        # Generate initial difficulty distribution (only if reports directory is specified)
        if [[ -n "$REPORTS_DIR" ]]; then
            log "Generating initial difficulty distribution..."
            local dist_dir="$REPORTS_DIR/difficulty_distribution"
            ensure_dir "$dist_dir"
            
            python "$script_dir/cal_difficulty.py" distribution \
                -i "$difficulty_output" \
                -o "$dist_dir/difficulty_distribution_original.json"
            log_success "Initial difficulty distribution generated"
        fi
        
        INPUT_FOR_NEXT_STEP="$difficulty_output"
    else
        log_warning "Skipping difficulty calculation step"
        # INPUT_FOR_NEXT_STEP remains the same from previous step
    fi
    
    # Step 3: Check for duplicates and remove them
    if [[ "$SKIP_DUPLICATE" == false ]]; then
        log "Step 3: Checking for duplicate configurations and removing duplicates..."
        
        # Generate duplicate reports (only if reports directory is specified)
        if [[ -n "$REPORTS_DIR" ]]; then
            local duplicate_dir="$REPORTS_DIR/check_duplicate"
            ensure_dir "$duplicate_dir"
            
            # Generate detailed duplicate report
            python "$script_dir/check_duplicate.py" detail \
                -i "$INPUT_FOR_NEXT_STEP" \
                -o "$duplicate_dir/duplicate_detail.txt"
            
            # Generate overview CSV report
            python "$script_dir/check_duplicate.py" overview \
                -i "$INPUT_FOR_NEXT_STEP" \
                -o "$duplicate_dir/duplicate_overview.csv"
        fi
        
        # Remove duplicates
        local deduplicated_output="$OUTPUT_DIR/3_deduplicated_data"
        ensure_dir "$deduplicated_output"
        
        python "$script_dir/deduplicate.py" -i "$INPUT_FOR_NEXT_STEP" -o "$deduplicated_output"
        log_success "Duplicate analysis and removal completed"
        
        # Generate post-deduplication difficulty distribution (only if reports directory is specified)
        if [[ "$SKIP_DIFFICULTY" == false && -n "$REPORTS_DIR" ]]; then
            log "Generating post-deduplication difficulty distribution..."
            python "$script_dir/cal_difficulty.py" distribution \
                -i "$deduplicated_output" \
                -o "$REPORTS_DIR/difficulty_distribution/difficulty_distribution_deduplicated.json"
            log_success "Post-deduplication difficulty distribution generated"
        fi
        
        INPUT_FOR_NEXT_STEP="$deduplicated_output"
    else
        log_warning "Skipping duplicate checking and removal"
    fi
    
    # Step 4: Split data
    if [[ "$SKIP_SPLIT" == false ]]; then
        log "Step 4: Splitting data into train/validate/test sets..."
        local split_output="$OUTPUT_DIR/4_splitted"
        ensure_dir "$split_output"
        
        python "$script_dir/split_rl.py" -i "$INPUT_FOR_NEXT_STEP" -o "$split_output"
        log_success "Data splitting completed"
    else
        log_warning "Skipping data splitting step"
    fi
    
    # Cleanup reports if not keeping them
    if [[ "$KEEP_REPORTS" == false && "$SKIP_DUPLICATE" == false && -n "$REPORTS_DIR" ]]; then
        log "Cleaning up intermediate report files..."
        # Keep only the summary files, remove detailed reports
        if [[ -f "$REPORTS_DIR/check_duplicate/duplicate_detail.txt" ]]; then
            rm "$REPORTS_DIR/check_duplicate/duplicate_detail.txt"
        fi
    fi
    
    log_success "Data transformation pipeline completed successfully!"
    echo ""
    echo "Output files:"
    if [[ "$SKIP_FORMAT" == false ]]; then
        echo "  - Formatted data: $INPUT_DIR/"
    fi
    if [[ "$SKIP_DIFFICULTY" == false ]]; then
        echo "  - Data with difficulty scores: $OUTPUT_DIR/2_data_with_difficulty/"
    fi
    if [[ "$SKIP_DUPLICATE" == false ]]; then
        echo "  - Deduplicated data: $OUTPUT_DIR/3_deduplicated_data/"
        if [[ -n "$REPORTS_DIR" ]]; then
            echo "  - Duplicate analysis: $REPORTS_DIR/check_duplicate/"
        fi
    fi
    if [[ "$SKIP_SPLIT" == false ]]; then
        echo "  - Train/validate/test splits: $OUTPUT_DIR/4_splitted/"
    fi
    if [[ "$SKIP_DIFFICULTY" == false && -n "$REPORTS_DIR" ]]; then
        echo "  - Difficulty distributions: $REPORTS_DIR/difficulty_distribution/"
    fi
}

# Main execution
main() {
    parse_args "$@"
    check_dependencies
    validate_input
    run_pipeline
}

# Run main function with all arguments
main "$@"