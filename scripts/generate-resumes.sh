#!/bin/bash
set -euo pipefail

# Resume Generator Script
# This script handles the main logic for generating resumes using resume-composer

# Function to print usage
usage() {
    echo "Usage: $0 --profiles-file PROFILES --config-file CONFIG --input-file INPUT [--name NAME] [--output-dir DIR] [--compile-latex] [--workspace-dir DIR] [--resume-composer-dir DIR]"
    echo ""
    echo "Options:"
    echo "  --profiles-file FILE      Path to profiles file (required)"
    echo "  --config-file FILE        Path to config file (required)"
    echo "  --input-file FILE         Path to input LaTeX file (required)"
    echo "  --name NAME               Name for resume files (default: John Doe)"
    echo "  --output-dir DIR          Output directory for generated resumes (default: current directory)"
    echo "  --compile-latex           Compile LaTeX files to PDF (optional)"
    echo "  --workspace-dir DIR       Workspace directory (default: workspace)"
    echo "  --resume-composer-dir DIR Resume composer directory (default: resume-composer)"
    echo "  --help                    Show this help message"
    exit 1
}

# Default values
WORKSPACE_DIR="workspace"
RESUME_COMPOSER_DIR="resume-composer"
COMPILE_LATEX=false
PROFILES_FILE=""
CONFIG_FILE=""
INPUT_FILE=""
NAME="John Doe"
OUTPUT_DIR=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profiles-file)
            PROFILES_FILE="$2"
            shift 2
            ;;
        --config-file)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --input-file)
            INPUT_FILE="$2"
            shift 2
            ;;
        --name)
            NAME="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --compile-latex)
            COMPILE_LATEX=true
            shift
            ;;
        --workspace-dir)
            WORKSPACE_DIR="$2"
            shift 2
            ;;
        --resume-composer-dir)
            RESUME_COMPOSER_DIR="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PROFILES_FILE" || -z "$CONFIG_FILE" || -z "$INPUT_FILE" ]]; then
    echo "Error: Missing required arguments"
    usage
fi

echo "=== Resume Generator Script ==="
echo "Profiles file: $PROFILES_FILE"
echo "Config file: $CONFIG_FILE"
echo "Input file: $INPUT_FILE"
echo "Compile LaTeX: $COMPILE_LATEX"
echo "Workspace directory: $WORKSPACE_DIR"
echo "Resume composer directory: $RESUME_COMPOSER_DIR"
echo ""

# Function to install resume-composer dependencies
install_dependencies() {
    echo "📦 Installing resume-composer dependencies..."
    cd "$RESUME_COMPOSER_DIR"
    python -m pip install --upgrade pip
    python -m pip install -e .
    cd - > /dev/null
    echo "✅ Dependencies installed successfully"
}

# Function to install LaTeX packages
install_latex() {
    if [[ "$COMPILE_LATEX" == true ]]; then
        echo "📄 Installing LaTeX packages..."
        sudo apt-get update -qq
        sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra
        echo "✅ LaTeX packages installed successfully"
    else
        echo "⏭️ Skipping LaTeX installation (compile-latex not enabled)"
    fi
}

# Function to verify input files exist
verify_files() {
    echo "🔍 Verifying input files..."
    cd "$WORKSPACE_DIR"

    local files_missing=false

    if [[ ! -f "$PROFILES_FILE" ]]; then
        echo "❌ Error: Profiles file '$PROFILES_FILE' not found"
        files_missing=true
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "❌ Error: Config file '$CONFIG_FILE' not found"
        files_missing=true
    fi

    if [[ ! -f "$INPUT_FILE" ]]; then
        echo "❌ Error: Input file '$INPUT_FILE' not found"
        files_missing=true
    fi

    if [[ "$files_missing" == true ]]; then
        echo "❌ One or more required files are missing"
        exit 1
    fi

    cd - > /dev/null
    echo "✅ All input files verified successfully"
}

# Function to clean output directory
clean_output_directory() {
    if [[ -n "$OUTPUT_DIR" ]]; then
        cd "$WORKSPACE_DIR"
        if [[ -d "$OUTPUT_DIR" ]]; then
            echo "🧹 Removing existing output directory: $OUTPUT_DIR"
            rm -rf "$OUTPUT_DIR"
            echo "✅ Output directory cleaned successfully"
        else
            echo "ℹ️ Output directory '$OUTPUT_DIR' does not exist, nothing to clean"
        fi
        cd - > /dev/null
    else
        echo "ℹ️ No output directory specified, skipping cleanup"
    fi
}

# Function to generate resumes
generate_resumes() {
    echo "🚀 Generating resumes..."
    cd "$WORKSPACE_DIR"

    # Set up Python path
    export PYTHONPATH="$(pwd)/../$RESUME_COMPOSER_DIR/src"

    # Build command
    local cmd="python -m resume_composer.generate_profiles --profiles '$PROFILES_FILE' --config '$CONFIG_FILE' --input '$INPUT_FILE' --name '$NAME'"

    if [[ -n "$OUTPUT_DIR" ]]; then
        cmd="$cmd --output-dir '$OUTPUT_DIR'"
    fi

    if [[ "$COMPILE_LATEX" == true ]]; then
        cmd="$cmd --compile"
    fi

    echo "Running: $cmd"
    eval "$cmd"

    cd - > /dev/null
    echo "✅ Resumes generated successfully"
}

# Function to list generated files
list_generated_files() {
    echo "📋 Listing generated files..."
    cd "$WORKSPACE_DIR"

    echo "Generated files:"
    # Find files newer than the input file, or if that fails, find common resume files
    if find . -name "*.tex" -newer "$INPUT_FILE" -o -name "*.pdf" -newer "$INPUT_FILE" 2>/dev/null | sort; then
        : # Command succeeded
    else
        echo "No files newer than input file found. Listing all .tex and .pdf files:"
        find . -name "*.tex" -o -name "*.pdf" 2>/dev/null | sort || echo "No .tex or .pdf files found"
    fi

    cd - > /dev/null
}

# Function to cleanup temporary files
cleanup() {
    echo "🧹 Cleaning up temporary files..."

    # Remove the resume-composer directory to avoid committing it
    if [[ -d "$RESUME_COMPOSER_DIR" ]]; then
        rm -rf "$RESUME_COMPOSER_DIR"
        echo "✅ Removed $RESUME_COMPOSER_DIR directory"
    fi

    # Could add other cleanup tasks here if needed
    echo "✅ Cleanup completed successfully"
}

# Main execution
main() {
    echo "🎯 Starting resume generation process..."

    install_dependencies
    install_latex
    verify_files
    clean_output_directory
    generate_resumes
    list_generated_files
    cleanup

    echo ""
    echo "🎉 Resume generation completed successfully!"
}

# Run main function
main "$@"