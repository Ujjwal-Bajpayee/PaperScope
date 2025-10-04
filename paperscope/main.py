from paperscope.arxiv_client import search_papers
import os

from paperscope.storage import add_entry, load_db

def fetch_and_summarize(keywords):
    """
    Search arXiv papers by keyword, summarize abstracts, and store results.
    """
    # Choose summarizer implementation at call time to avoid importing
    # heavy external clients during module import (prevents credential errors)
    if os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        from paperscope.summarizer_demo import summarize
    else:
        from paperscope.summarizer import summarize

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

def query_db(query):
    """
    Perform simple keyword search on stored summaries.
    """
    db = load_db()
    return [item for item in db if query.lower() in item["summary"].lower()]
