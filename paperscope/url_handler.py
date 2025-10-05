import re
import requests
import tempfile
import os
from typing import Optional, Tuple


def is_url(text: str) -> bool:
    """Check if the input text is a URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))


def extract_arxiv_id(url: str) -> Optional[str]:
    """Extract arXiv ID from various arXiv URL formats."""
    # Support various arXiv URL formats:
    # https://arxiv.org/abs/2301.12345
    # https://arxiv.org/pdf/2301.12345.pdf
    # http://arxiv.org/abs/2301.12345v1
    patterns = [
        r'arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)',
        r'arxiv\.org/pdf/([0-9]{4}\.[0-9]{4,5})(?:\.pdf)?',
        r'arxiv\.org/abs/([a-z\-]+/[0-9]{7})',  # Old format like cs/0123456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            arxiv_id = match.group(1)
            # Remove version suffix if present for consistent ID
            arxiv_id = re.sub(r'v[0-9]+$', '', arxiv_id)
            return arxiv_id
    return None


def download_pdf_from_url(url: str) -> Optional[str]:
    """
    Download a PDF from a URL and save it to a temporary file.
    Returns the path to the temporary file, or None if download fails.
    """
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Check if the response is actually a PDF
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type and not url.endswith('.pdf'):
            # Try to see if content starts with PDF magic bytes
            if not response.content.startswith(b'%PDF'):
                return None
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        print(f"Error downloading PDF from URL: {e}")
        return None


def get_arxiv_pdf_url(arxiv_id: str) -> str:
    """Convert arXiv ID to PDF download URL."""
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def fetch_paper_from_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Fetch paper from URL. Returns (paper_id, title, pdf_path).
    
    For arXiv URLs, extracts the ID and downloads the PDF.
    For direct PDF URLs, downloads the PDF.
    Returns None values if fetching fails.
    """
    try:
        # Check if it's an arXiv URL
        arxiv_id = extract_arxiv_id(url)
        if arxiv_id:
            # Fetch paper metadata from arXiv
            try:
                import arxiv
                search = arxiv.Search(id_list=[arxiv_id])
                result = next(search.results())
                
                # Download PDF
                pdf_url = get_arxiv_pdf_url(arxiv_id)
                pdf_path = download_pdf_from_url(pdf_url)
                
                if pdf_path:
                    return (result.entry_id, result.title, pdf_path)
                else:
                    return (result.entry_id, result.title, None)
            except Exception as e:
                print(f"Error fetching arXiv paper: {e}")
                # Try to download PDF directly even if metadata fetch fails
                pdf_url = get_arxiv_pdf_url(arxiv_id)
                pdf_path = download_pdf_from_url(pdf_url)
                if pdf_path:
                    return (arxiv_id, f"arXiv:{arxiv_id}", pdf_path)
                return None, None, None
        
        # If it's a direct PDF URL, try to download it
        if url.lower().endswith('.pdf') or 'pdf' in url.lower():
            pdf_path = download_pdf_from_url(url)
            if pdf_path:
                # Extract a basic title from URL
                title = url.split('/')[-1].replace('.pdf', '').replace('_', ' ').replace('-', ' ')
                return (url, title, pdf_path)
        
        return None, None, None
    except Exception as e:
        print(f"Error in fetch_paper_from_url: {e}")
        return None, None, None
