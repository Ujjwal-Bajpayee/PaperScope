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
    try:
        # Validate input
        if not keywords or not keywords.strip():
            raise ValueError("Please provide keywords or a paper URL to search.")
        
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
        try:
            results = search_papers(keywords, max_results=5)
        except Exception as e:
            raise Exception(f"Failed to search arXiv: {str(e)}. Please check your internet connection and try again.")
        
        if not results:
            raise Exception(f"No papers found for keywords: '{keywords}'. Try different keywords or check spelling.")
        
        processed_count = 0
        for pid, title, abstract in results:
            try:
                summary = summarize(abstract)
                entry = {
                    "id": pid,
                    "title": title,
                    "abstract": abstract,
                    "summary": summary
                }
                add_entry(entry)
                processed_count += 1
            except Exception as e:
                print(f"Warning: Failed to process paper '{title}': {str(e)}")
                continue
        
        if processed_count == 0:
            raise Exception("Failed to process any papers. Please try again.")
        
        return load_db()
    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")


def fetch_and_summarize_from_url(url):
    """
    Fetch paper from URL, extract text, summarize, and store result.
    Handles arXiv URLs and direct PDF links.
    """
    try:
        # Validate URL
        if not url or not url.strip():
            raise ValueError("Please provide a valid URL.")
        
        if os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"):
            from paperscope.summarizer_demo import summarize
        else:
            from paperscope.summarizer import summarize
        
        try:
            paper_id, title, pdf_path = fetch_paper_from_url(url)
        except Exception as e:
            raise Exception(f"Failed to fetch paper from URL: {str(e)}. Please check the URL and try again.")
        
        if not paper_id:
            raise ValueError("Failed to extract paper ID from URL. Please check the URL format. Supported formats: arXiv URLs (abs or pdf) and direct PDF links.")
        
        if not pdf_path:
            raise ValueError("Failed to download PDF from URL. The URL may be invalid, the server may be unavailable, or the file may not exist.")
        
        try:
            # Extract text from the PDF
            text = extract_text_from_pdf(pdf_path)
            
            if not text or len(text.strip()) == 0:
                raise ValueError("Failed to extract text from PDF. The PDF may be empty, corrupted, or password-protected.")
            
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
    except Exception as e:
        raise Exception(f"URL processing failed: {str(e)}")

def query_db(query):
    """
    Perform simple keyword search on stored summaries.
    """
    try:
        if not query or not query.strip():
            raise ValueError("Please provide a search query.")
        
        db = load_db()
        if not db:
            raise Exception("No papers found in database. Please add some papers first.")
        
        results = [item for item in db if query.lower() in item["summary"].lower()]
        return results
    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")
