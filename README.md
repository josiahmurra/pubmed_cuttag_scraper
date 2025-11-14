# PubMed CUT&Tag Peak Caller Scraper

This tool automatically searches PubMed for papers using CUT&Tag methodology and identifies the peak calling software they use by extracting text following "peak calling" mentions.

## Features

- **Automated PubMed Search**: Uses NCBI's E-utilities API to search for CUT&Tag papers
- **Intelligent Text Extraction**: Identifies peak calling software mentions using pattern matching
- **Multiple Output Formats**: Saves results as both CSV and JSON files
- **Comprehensive Analysis**: Extracts titles, abstracts, authors, and publication details
- **Peak Caller Detection**: Recognizes common peak calling tools like MACS2, SEACR, GoPeaks, HOMER, etc.

## Installation

1. **Install Python 3** (if not already installed)
2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

### Quick Start

```bash
# Make the runner script executable (if not already)
chmod +x run_cuttag_scraper.sh

# Run with your email address
./run_cuttag_scraper.sh your.email@university.edu
```

### Advanced Usage

```bash
# Run with custom parameters
python3 pubmed_cuttag_peakcaller_scraper.py \
    --email your.email@university.edu \
    --max-results 200 \
    --output my_cuttag_analysis \
    --query "CUT&Tag AND histone"
```

### Command Line Options

- `--email`: Your email address (required by NCBI)
- `--api-key`: Optional NCBI API key for higher rate limits
- `--max-results`: Maximum number of papers to analyze (default: 100)
- `--output`: Output file prefix (default: cuttag_peakcaller_results)
- `--query`: Custom PubMed search query (default: "CUT&Tag OR CUT and Tag")

## Output Files

The script generates timestamped output files:

- `{output_prefix}_{timestamp}.csv`: Spreadsheet format with all results
- `{output_prefix}_{timestamp}.json`: JSON format for programmatic access

### CSV Columns

- `pmid`: PubMed ID
- `title`: Paper title
- `abstract`: Paper abstract
- `authors`: Author list (first 5 authors)
- `journal`: Journal name
- `publication_date`: Publication date
- `peak_calling_mentions`: Raw text mentions of peak calling
- `identified_peak_callers`: Specific software identified
- `peak_calling_summary`: Human-readable summary

## Peak Caller Detection

The script identifies peak calling software using:

1. **Pattern Matching**: Looks for phrases like "peak calling:", "peaks were called", etc.
2. **Known Software**: Recognizes common tools:
   - MACS2/MACS/MACS3
   - SEACR
   - GoPeaks
   - HOMER
   - PeakSeq, SICER, ZINBA, PePr, Genrich, SPP, PeakRanger, F-seq, QuEST, CisGenome, FindPeaks

## Example Results

```
Summary:
Total papers analyzed: 50
Papers with identified peak callers: 23
Papers with peak calling mentions: 35

Peak caller usage:
  MACS2: 12 papers
  SEACR: 8 papers
  HOMER: 5 papers
  GoPeaks: 3 papers
```

## Customization

### Adding New Peak Callers

Edit the `peak_callers` list in the script:

```python
self.peak_callers = [
    'MACS2', 'MACS', 'MACS3', 'SEACR', 'GoPeaks', 'HOMER',
    'YourNewPeakCaller'  # Add here
]
```

### Modifying Search Patterns

Update the `peak_calling_patterns` list:

```python
self.peak_calling_patterns = [
    r'peak calling[:\s]+([^.,;]+)',
    r'your custom pattern here'  # Add here
]
```

## API Rate Limits

- **Without API key**: 3 requests per second
- **With API key**: 10 requests per second

Get a free API key at: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

## Troubleshooting

### Common Issues

1. **"No papers found"**: Try broadening your search query
2. **Rate limit errors**: Add delays or get an API key
3. **XML parsing errors**: Usually temporary, try running again

### Debug Mode

Add print statements to see what's happening:

```python
print(f"Searching for: {query}")
print(f"Found {len(pmids)} papers")
```

## Legal and Ethical Considerations

- **NCBI Terms of Service**: Always provide your email address
- **Rate Limits**: Respect API limits to avoid being blocked
- **Attribution**: Cite papers appropriately in your research
- **Data Usage**: Use results responsibly and ethically

## Contributing

Feel free to improve the script by:
- Adding more peak caller detection patterns
- Improving text extraction accuracy
- Adding support for other databases
- Enhancing output formatting

## License

This script is provided as-is for research purposes. Please respect NCBI's terms of service and use responsibly.
