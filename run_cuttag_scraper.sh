#!/bin/bash

# PubMed CUT&Tag Peak Caller Scraper Runner
# This script sets up and runs the PubMed scraper

echo "PubMed CUT&Tag Peak Caller Scraper"
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Install requirements
echo "Installing Python requirements..."
pip3 install -r requirements.txt

# Make the script executable
chmod +x pubmed_cuttag_peakcaller_scraper.py

# Check if email is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <your-email@example.com> [max-results] [output-prefix]"
    echo ""
    echo "Examples:"
    echo "  $0 john.doe@university.edu"
    echo "  $0 john.doe@university.edu 50"
    echo "  $0 john.doe@university.edu 100 my_cuttag_analysis"
    echo ""
    echo "Note: Your email is required by NCBI's terms of service"
    exit 1
fi

EMAIL="$1"
MAX_RESULTS="${2:-100}"
OUTPUT_PREFIX="${3:-cuttag_peakcaller_results}"

echo "Starting PubMed search for CUT&Tag papers..."
echo "Email: $EMAIL"
echo "Max results: $MAX_RESULTS"
echo "Output prefix: $OUTPUT_PREFIX"
echo ""

# Run the scraper
python3 pubmed_cuttag_peakcaller_scraper.py \
    --email "$EMAIL" \
    --max-results "$MAX_RESULTS" \
    --output "$OUTPUT_PREFIX"

echo ""
echo "Analysis complete! Check the generated CSV and JSON files for results."
