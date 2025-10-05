from paperscope.arxiv_client import search_papers
from paperscope.url_handler import is_url, fetch_paper_from_url
from paperscope.pdf_parser import extract_text_from_pdf
import os

from paperscope.storage import add_entry, load_db

def fetch_and_summarize(keywords):
    """
    Search arXiv papers by keyword, summarize abstracts, and store results.
    Also supports paper URLs (arXiv or direct PDF links).
    """
    # Choose summarizer implementation at call time to avoid importing
    # heavy external clients during module import (prevents credential errors)
    if os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        from paperscope.summarizer_demo import summarize
    else:
        from paperscope.summarizer import summarize

    # Check if input is a URL
    if is_url(keywords):
        return fetch_and_summarize_from_url(keywords)
    
    # Otherwise, proceed with keyword search
    results = search_papers(keywords, max_results=5)
    for pid, title, abstract in results:
        summary = summarize(abstract)
        entry = {
            "id": pid,
            "title": title,
            "abstract": abstract,
            "summary": summary
        }
        add_entry(entry)
    return load_db()


def fetch_and_summarize_from_url(url):
    """
    Fetch paper from URL, extract text, summarize, and store result.
    Handles arXiv URLs and direct PDF links.
    """
    if os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        from paperscope.summarizer_demo import summarize
    else:
        from paperscope.summarizer import summarize
    
    paper_id, title, pdf_path = fetch_paper_from_url(url)
    
    if not paper_id:
        raise ValueError("Failed to extract paper ID from URL. Please check the URL format.")
    
    if not pdf_path:
        raise ValueError("Failed to download PDF from URL. The URL may be invalid or the server may be unavailable.")
    
    try:
        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) == 0:
            raise ValueError("Failed to extract text from PDF. The PDF may be empty or corrupted.")
        
        # Summarize the extracted text
        summary = summarize(text)
        
        # Store the entry
        entry = {
            "id": paper_id,
            "title": title,
            "abstract": text[:500] + "...",  # Store first 500 chars as abstract
            "summary": summary
        }
        add_entry(entry)
        
        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        return load_db()
    except Exception as e:
        # Clean up the temporary PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except:
                pass
        # Re-raise the exception with context
        raise Exception(f"Error processing paper from URL: {str(e)}") from e

def query_db(query):
    """
    Perform simple keyword search on stored summaries.
    """
    db = load_db()
    return [item for item in db if query.lower() in item["summary"].lower()]
