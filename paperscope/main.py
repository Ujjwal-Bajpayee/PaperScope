from paperscope.arxiv_client import search_papers
from paperscope.summarizer import summarize
from paperscope.storage import add_entry, load_db

def fetch_and_summarize(keywords):
    """
    Search arXiv papers by keyword, summarize abstracts, and store results.
    """
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
