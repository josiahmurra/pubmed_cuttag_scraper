#!/usr/bin/env python3
"""
PubMed CUT&Tag Peak Caller Scraper

This script searches PubMed for papers using CUT&Tag methodology and identifies
the peak calling software they use by extracting text following "peak calling"
mentions.

Author: Generated for bioinformatics automation
Date: 2024
"""

import requests
import xml.etree.ElementTree as ET
import time
import re
import json
import csv
from typing import List, Dict, Optional
from urllib.parse import quote
import argparse
from datetime import datetime

class PubMedCUTTagScraper:
    def __init__(self, email: str = "your.email@example.com", api_key: Optional[str] = None):
        """
        Initialize the PubMed scraper.
        
        Args:
            email: Your email address (required by NCBI)
            api_key: Optional API key for higher rate limits
        """
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.pmc_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email
        self.api_key = api_key
        self.session = requests.Session()
        
        # Common peak calling software patterns
        self.peak_callers = [
            'MACS2', 'MACS', 'MACS3', 'SEACR', 'GoPeaks', 'HOMER', 'PeakSeq',
            'SICER', 'ZINBA', 'PePr', 'Genrich', 'SPP', 'PeakRanger',
            'F-seq', 'QuEST', 'CisGenome', 'FindPeaks'
        ]
        
        # Patterns to look for peak calling mentions
        self.peak_calling_patterns = [
            r'peak calling[:\s]+([^.,;]+)',
            r'peaks were called[:\s]+([^.,;]+)',
            r'peak detection[:\s]+([^.,;]+)',
            r'identified peaks[:\s]+([^.,;]+)',
            r'peak identification[:\s]+([^.,;]+)',
            r'using\s+([^.,;]*peak[^.,;]*)',
            r'([^.,;]*peak[^.,;]*)\s+was used',
            r'([^.,;]*peak[^.,;]*)\s+software',
            r'([^.,;]*peak[^.,;]*)\s+algorithm'
        ]

    def search_pubmed(self, query: str, max_results: int = 100, year: int = None) -> List[str]:
        """
        Search PubMed for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            year: Optional year filter (e.g., 2019)
            
        Returns:
            List of PubMed IDs
        """
        print(f"Searching PubMed for: {query}")
        
        # For CUT&Tag, use proper ampersand encoding
        if 'CUT&Tag' in query:
            query = query.replace('CUT&Tag', 'CUT%26amp;Tag')
            print(f"Using proper ampersand encoding: {query}")
            # Don't double-encode since we already encoded the ampersand
            encoded_query = query
        else:
            # URL encode the query
            encoded_query = quote(query)
        
        # Add year filter if specified
        if year:
            encoded_query = f"{encoded_query} AND {year}[PDAT]"
            print(f"Filtering by year: {year}")
        
        # Build the search URL
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': encoded_query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            total_found = data.get('esearchresult', {}).get('count', 0)
            
            print(f"Found {len(pmids)} papers (total available: {total_found})")
            return pmids
            
        except requests.RequestException as e:
            print(f"Error searching PubMed: {e}")
            # Check if it's a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("\n⚠️  API rate limit exceeded during PubMed search!")
                print("The script will now exit to avoid wasting time.")
                print("Please wait a few minutes before running the script again.")
                exit(1)
            return []

    def search_pmc(self, query: str, max_results: int = 100, year: int = None) -> List[str]:
        """
        Search PMC for papers matching the query and return corresponding PubMed IDs.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            year: Optional year filter (e.g., 2019)
            
        Returns:
            List of PubMed IDs
        """
        print(f"Searching PMC for: {query}")
        
        # For CUT&Tag, use proper ampersand encoding
        if 'CUT&Tag' in query:
            query = query.replace('CUT&Tag', 'CUT%26amp;Tag')
            print(f"Using proper ampersand encoding: {query}")
            # Don't double-encode since we already encoded the ampersand
            encoded_query = query
        else:
            # URL encode the query
            encoded_query = quote(query)
        
        # Add year filter if specified
        if year:
            encoded_query = f"{encoded_query} AND {year}[PDAT]"
            print(f"Filtering by year: {year}")
        
        # Search PMC first
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pmc',
            'term': encoded_query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pmc_ids = data.get('esearchresult', {}).get('idlist', [])
            total_found = data.get('esearchresult', {}).get('count', 0)
            
            print(f"Found {len(pmc_ids)} PMC papers (total available: {total_found})")
            
            if not pmc_ids:
                return []
            
            # Get corresponding PubMed IDs
            elink_url = f"{self.base_url}elink.fcgi"
            elink_params = {
                'dbfrom': 'pmc',
                'db': 'pubmed',
                'id': ','.join(pmc_ids),
                'retmode': 'json',
                'email': self.email
            }
            
            if self.api_key:
                elink_params['api_key'] = self.api_key
                
            elink_response = self.session.get(elink_url, params=elink_params)
            elink_response.raise_for_status()
            
            elink_data = elink_response.json()
            pmids = []
            
            for linkset in elink_data.get('linksets', []):
                linksetdbs = linkset.get('linksetdbs', [])
                for linksetdb in linksetdbs:
                    if linksetdb.get('linkname') == 'pmc_pubmed':
                        pmids.extend(linksetdb.get('links', []))
            
            print(f"Found {len(pmids)} corresponding PubMed IDs")
            return pmids
            
        except requests.RequestException as e:
            print(f"Error searching PMC: {e}")
            # Check if it's a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("\n⚠️  API rate limit exceeded during PMC search!")
                print("The script will now exit to avoid wasting time.")
                print("Please wait a few minutes before running the script again.")
                exit(1)
            return []

    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch abstracts and metadata for given PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of dictionaries containing paper information
        """
        if not pmids:
            return []
            
        print(f"Fetching abstracts for {len(pmids)} papers...")
        
        # Split into batches to avoid URL length limits
        batch_size = 200
        all_papers = []
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i + batch_size]
            
            fetch_url = f"{self.base_url}efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': ','.join(batch_pmids),
                'retmode': 'xml',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
                
            try:
                response = self.session.get(fetch_url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                papers = self._parse_xml_papers(root)
                all_papers.extend(papers)
                
                # Be nice to the API
                time.sleep(0.1)
                
            except requests.RequestException as e:
                print(f"Error fetching abstracts: {e}")
                # Check if it's a rate limit error
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("\n⚠️  API rate limit exceeded during abstract fetching!")
                    print("The script will now exit to avoid wasting time.")
                    print("Please wait a few minutes before running the script again.")
                    exit(1)
                continue
            except ET.ParseError as e:
                print(f"Error parsing XML: {e}")
                continue
                
        return all_papers

    def check_pmc_availability(self, pmids: List[str]) -> Dict[str, str]:
        """
        Check which papers have PMC full text available.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dictionary mapping PMID to PMC ID if available
        """
        if not pmids:
            return {}
            
        print(f"Checking PMC availability for {len(pmids)} papers...")
        
        # Check PMC availability one paper at a time to avoid rate limits
        batch_size = 1
        pmc_mapping = {}
        
        for i, pmid in enumerate(pmids):
            print(f"Checking PMC availability for paper {i+1}/{len(pmids)} (PMID: {pmid})...")
            
            # Use elink to find PMC IDs
            elink_url = f"{self.base_url}elink.fcgi"
            params = {
                'dbfrom': 'pubmed',
                'db': 'pmc',
                'id': pmid,
                'retmode': 'json',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
                
            try:
                response = self.session.get(elink_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                linksets = data.get('linksets', [])
                
                for linkset in linksets:
                    pmid = linkset.get('ids', [''])[0]
                    linksetdbs = linkset.get('linksetdbs', [])
                    
                    # Look for the main PMC link (not references)
                    for linksetdb in linksetdbs:
                        if linksetdb.get('linkname') == 'pubmed_pmc':
                            pmc_ids = linksetdb.get('links', [])
                            if pmc_ids:
                                pmc_mapping[pmid] = pmc_ids[0]
                            break
                
                time.sleep(2.5)  # Be patient with the API to avoid rate limits
                
            except requests.RequestException as e:
                print(f"Error checking PMC availability: {e}")
                # Check if it's a rate limit error
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("\n⚠️  API rate limit exceeded!")
                    print("The script will now exit to avoid wasting time.")
                    print("Please wait a few minutes before running the script again.")
                    return pmc_mapping
                continue
            
            # Add delay between each paper
            if i < len(pmids) - 1:
                time.sleep(2.5)
        
        print(f"Found {len(pmc_mapping)} papers with PMC full text available")
        return pmc_mapping

    def fetch_pmc_full_text(self, pmc_id: str) -> str:
        """
        Fetch full text from PMC.
        
        Args:
            pmc_id: PMC ID
            
        Returns:
            Full text content
        """
        fetch_url = f"{self.pmc_base_url}efetch.fcgi"
        params = {
            'db': 'pmc',
            'id': pmc_id,
            'retmode': 'xml',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        try:
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()
            
            # Parse XML and extract text content
            root = ET.fromstring(response.content)
            
            # Extract text from all text nodes
            full_text = ""
            for elem in root.iter():
                if elem.text:
                    full_text += elem.text + " "
                if elem.tail:
                    full_text += elem.tail + " "
            
            time.sleep(1.0)  # Be nice to the API
            return full_text.strip()
            
        except requests.RequestException as e:
            print(f"Error fetching PMC full text for {pmc_id}: {e}")
            # Check if it's a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("\n⚠️  API rate limit exceeded during PMC text fetching!")
                print("The script will now exit to avoid wasting time.")
                print("Please wait a few minutes before running the script again.")
                exit(1)
            return ""
        except ET.ParseError as e:
            print(f"Error parsing PMC XML for {pmc_id}: {e}")
            return ""

    def _parse_xml_papers(self, root: ET.Element) -> List[Dict]:
        """Parse XML response from PubMed into paper dictionaries."""
        papers = []
        
        for article in root.findall('.//PubmedArticle'):
            paper = {}
            
            # Extract PMID
            pmid_elem = article.find('.//PMID')
            paper['pmid'] = pmid_elem.text if pmid_elem is not None else 'Unknown'
            
            # Extract title
            title_elem = article.find('.//ArticleTitle')
            paper['title'] = title_elem.text if title_elem is not None else 'No title'
            
            # Extract abstract
            abstract_elem = article.find('.//AbstractText')
            paper['abstract'] = abstract_elem.text if abstract_elem is not None else 'No abstract'
            
            # Extract authors
            authors = []
            for author in article.findall('.//Author'):
                last_name = author.find('LastName')
                first_name = author.find('ForeName')
                if last_name is not None:
                    author_name = last_name.text
                    if first_name is not None:
                        author_name += f" {first_name.text}"
                    authors.append(author_name)
            paper['authors'] = ', '.join(authors[:5])  # Limit to first 5 authors
            
            # Extract journal
            journal_elem = article.find('.//Journal/Title')
            paper['journal'] = journal_elem.text if journal_elem is not None else 'Unknown journal'
            
            # Extract publication date
            pub_date = article.find('.//PubDate')
            if pub_date is not None:
                year = pub_date.find('Year')
                month = pub_date.find('Month')
                day = pub_date.find('Day')
                date_parts = []
                if year is not None:
                    date_parts.append(year.text)
                if month is not None:
                    date_parts.append(month.text)
                if day is not None:
                    date_parts.append(day.text)
                paper['publication_date'] = ' '.join(date_parts)
            else:
                paper['publication_date'] = 'Unknown date'
            
            papers.append(paper)
            
        return papers

    def extract_peak_calling_info(self, text: str) -> List[str]:
        """
        Extract peak calling software mentions from text.
        
        Args:
            text: Text to search (abstract, title, etc.)
            
        Returns:
            List of potential peak calling software mentions
        """
        mentions = []
        text_lower = text.lower()
        
        # Look for specific patterns
        for pattern in self.peak_calling_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                mention = match.group(1).strip()
                if mention and len(mention) < 100:  # Reasonable length filter
                    mentions.append(mention)
        
        # Also look for direct mentions of known peak callers
        for caller in self.peak_callers:
            if caller.lower() in text_lower:
                # Find the context around the mention
                pattern = rf'.{{0,50}}{re.escape(caller.lower())}.{{0,50}}'
                context_matches = re.findall(pattern, text_lower)
                for context in context_matches:
                    # Filter out common false positives
                    if not self._is_false_positive(context, caller):
                        mentions.append(context.strip())
        
        return list(set(mentions))  # Remove duplicates

    def extract_cuttag_mentions(self, text: str) -> List[str]:
        """
        Extract CUT&Tag methodology mentions from text.
        
        Args:
            text: Text to search (abstract, title, full text, etc.)
            
        Returns:
            List of CUT&Tag methodology mentions
        """
        mentions = []
        text_lower = text.lower()
        
        # CUT&Tag related patterns
        cuttag_patterns = [
            r'cut&tag',
            r'cut and tag',
            r'cut-tag',
            r'cuttag',
            r'cleavage under targets and tagmentation',
            r'cleavage under targets & tagmentation'
        ]
        
        for pattern in cuttag_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Get context around the mention
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                if context and len(context) < 200:  # Reasonable length filter
                    mentions.append(context)
        
        return list(set(mentions))  # Remove duplicates

    def extract_chipseq_mentions(self, text: str) -> List[str]:
        """
        Extract ChIP-seq methodology mentions from text.
        
        Args:
            text: Text to search (abstract, title, full text, etc.)
            
        Returns:
            List of ChIP-seq methodology mentions
        """
        mentions = []
        text_lower = text.lower()
        
        # ChIP-seq related patterns
        chipseq_patterns = [
            r'chip-seq',
            r'chipseq',
            r'chromatin immunoprecipitation',
            r'chromatin immunoprecipitation sequencing',
            r'chip sequencing',
            r'immunoprecipitation.*sequencing',
            r'ip.*seq',
            r'chip.*seq'
        ]
        
        for pattern in chipseq_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Get context around the mention
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                if context and len(context) < 200:  # Reasonable length filter
                    mentions.append(context)
        
        return list(set(mentions))  # Remove duplicates

    def _is_false_positive(self, context: str, caller: str) -> bool:
        """
        Check if a peak caller mention is likely a false positive.
        
        Args:
            context: The text context around the mention
            caller: The peak caller name
            
        Returns:
            True if this is likely a false positive
        """
        context_lower = context.lower()
        
        # Common false positive patterns
        false_positive_patterns = {
            'quest': ['question', 'questionnaire', 'request', 'conquest'],
            'macs': ['macintosh', 'mac address', 'macbook'],
            'homer': ['homer simpson', 'homeric', 'homerun'],
            'peaks': ['mountain peaks', 'peak performance', 'peak hours'],
        }
        
        if caller.lower() in false_positive_patterns:
            for pattern in false_positive_patterns[caller.lower()]:
                if pattern in context_lower:
                    return True
        
        # Check if it's in a methods/peak calling context
        methods_keywords = ['peak', 'calling', 'detection', 'identification', 'analysis', 'software', 'tool', 'algorithm', 'method']
        if any(keyword in context_lower for keyword in methods_keywords):
            return False
        
        # If no methods context, likely false positive
        return True

    def analyze_papers(self, papers: List[Dict], pmc_mapping: Dict[str, str] = None) -> List[Dict]:
        """
        Analyze papers to extract peak calling information.
        
        Args:
            papers: List of paper dictionaries
            pmc_mapping: Dictionary mapping PMID to PMC ID for full text access
            
        Returns:
            List of papers with peak calling information added
        """
        print("Analyzing papers for peak calling information...")
        
        if pmc_mapping is None:
            pmc_mapping = {}
        
        for i, paper in enumerate(papers):
            title = paper.get('title', 'No title')
            if title is None:
                title = 'No title'
            print(f"Analyzing paper {i+1}/{len(papers)}: {title[:50]}...")
            
            # Start with title and abstract
            paper_title = paper.get('title', 'No title') or 'No title'
            paper_abstract = paper.get('abstract', 'No abstract') or 'No abstract'
            full_text = f"{paper_title} {paper_abstract}"
            text_source = "abstract"
            
            # If PMC full text is available, use it instead
            pmid = paper['pmid']
            if pmid in pmc_mapping:
                pmc_id = pmc_mapping[pmid]
                pmc_text = self.fetch_pmc_full_text(pmc_id)
                if pmc_text:
                    full_text = pmc_text
                    text_source = "full_text"
                    print(f"  Using PMC full text (PMC{pmc_id})")
                else:
                    print(f"  PMC full text not available, using abstract")
            else:
                print(f"  No PMC access, using abstract")
            
            # Extract peak calling mentions
            peak_mentions = self.extract_peak_calling_info(full_text)
            paper['peak_calling_mentions'] = peak_mentions
            paper['text_source'] = text_source
            
            # Extract CUT&Tag methodology mentions
            cuttag_mentions = self.extract_cuttag_mentions(full_text)
            paper['cuttag_mentions'] = cuttag_mentions
            paper['has_cuttag'] = len(cuttag_mentions) > 0
            
            # Extract ChIP-seq methodology mentions
            chipseq_mentions = self.extract_chipseq_mentions(full_text)
            paper['chipseq_mentions'] = chipseq_mentions
            paper['has_chipseq'] = len(chipseq_mentions) > 0
            
            # Add PubMed link for easy access
            paper['pubmed_link'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # Extract year from publication date
            publication_date = paper.get('publication_date', '')
            year = 'Unknown'
            if publication_date and publication_date != 'Unknown date':
                # Try to extract year from various date formats
                year_match = re.search(r'\b(20\d{2})\b', publication_date)
                if year_match:
                    year = year_match.group(1)
            paper['year_published'] = year
            
            # Try to identify specific software
            identified_software = []
            for mention in peak_mentions:
                for caller in self.peak_callers:
                    if caller.lower() in mention.lower():
                        # Normalize variants to their main software
                        if caller.lower() in ['macs2', 'macs3']:
                            identified_software.append('MACS')
                        elif caller.lower() == 'findpeaks':
                            identified_software.append('HOMER')
                        else:
                            identified_software.append(caller)
            
            paper['identified_peak_callers'] = list(set(identified_software))
            
            # Add a summary
            if paper['identified_peak_callers']:
                paper['peak_calling_summary'] = f"Uses: {', '.join(paper['identified_peak_callers'])}"
            elif paper['peak_calling_mentions']:
                paper['peak_calling_summary'] = f"Possible mentions: {', '.join(paper['peak_calling_mentions'][:3])}"
            else:
                paper['peak_calling_summary'] = "No clear peak calling method identified"
            
            # Be nice to the API
            time.sleep(0.2)
        
        return papers

    def save_results(self, papers: List[Dict], output_file: str, year: int = None, query: str = None):
        """
        Save results to CSV and JSON files.
        
        Args:
            papers: List of analyzed papers
            output_file: Base filename for output files
            year: Optional year filter for filename
            query: Optional query for filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build filename with year and query info
        filename_parts = [output_file]
        if year:
            filename_parts.append(f"year{year}")
        if query and query != "CUT&Tag OR \"CUT and Tag\"":
            # Clean up query for filename
            clean_query = query.replace(" ", "_").replace("&", "and").replace('"', "").replace("(", "").replace(")", "")
            filename_parts.append(clean_query[:20])  # Limit length
        
        base_filename = "_".join(filename_parts)
        
        # Save as CSV
        csv_file = f"{base_filename}_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if papers:
                writer = csv.DictWriter(f, fieldnames=papers[0].keys())
                writer.writeheader()
                writer.writerows(papers)
        print(f"Results saved to {csv_file}")
        
        # Save as JSON
        json_file = f"{base_filename}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        print(f"Results also saved to {json_file}")
        
        # Print summary statistics
        total_papers = len(papers)
        papers_with_peak_callers = len([p for p in papers if p['identified_peak_callers']])
        papers_with_mentions = len([p for p in papers if p['peak_calling_mentions']])
        papers_with_cuttag_mentions = len([p for p in papers if p['cuttag_mentions']])
        papers_with_chipseq_mentions = len([p for p in papers if p['chipseq_mentions']])
        
        print(f"\nSummary:")
        print(f"Total papers analyzed: {total_papers}")
        print(f"Papers with identified peak callers: {papers_with_peak_callers}")
        print(f"Papers with peak calling mentions: {papers_with_mentions}")
        print(f"Papers with CUT&Tag methodology mentions: {papers_with_cuttag_mentions}")
        print(f"Papers with ChIP-seq methodology mentions: {papers_with_chipseq_mentions}")
        
        # Count peak caller usage
        caller_counts = {}
        for paper in papers:
            for caller in paper['identified_peak_callers']:
                caller_counts[caller] = caller_counts.get(caller, 0) + 1
        
        if caller_counts:
            print(f"\nPeak caller usage:")
            for caller, count in sorted(caller_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {caller}: {count} papers")

def main():
    parser = argparse.ArgumentParser(description='Scrape PubMed for CUT&Tag papers and identify peak calling methods')
    parser.add_argument('--email', required=True, help='Your email address (required by NCBI)')
    parser.add_argument('--api-key', help='NCBI API key for higher rate limits (optional)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum number of papers to analyze')
    parser.add_argument('--year', type=int, help='Filter papers by publication year (e.g., 2019)')
    parser.add_argument('--output', default='cuttag_peakcaller_results', help='Output file prefix')
    parser.add_argument('--query', default='CUT&Tag OR "CUT and Tag"', help='PubMed search query')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = PubMedCUTTagScraper(email=args.email, api_key=args.api_key)
    
    # Search for papers (try PMC first, then PubMed)
    pmids = scraper.search_pmc(args.query, args.max_results, args.year)
    if not pmids:
        print("No PMC results found, trying PubMed search...")
        pmids = scraper.search_pubmed(args.query, args.max_results, args.year)
    
    if not pmids:
        print("No papers found. Exiting.")
        return
    
    # Fetch abstracts
    papers = scraper.fetch_abstracts(pmids)
    
    if not papers:
        print("No papers retrieved. Exiting.")
        return
    
    # Check for PMC full text availability
    pmc_mapping = scraper.check_pmc_availability(pmids)
    
    # Analyze for peak calling information (using full text when available)
    analyzed_papers = scraper.analyze_papers(papers, pmc_mapping)
    
    # Save results
    scraper.save_results(analyzed_papers, args.output, args.year, args.query)

if __name__ == "__main__":
    main()
