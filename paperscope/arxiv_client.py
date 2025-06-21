import arxiv

def search_papers(keywords, max_results):
    query = " AND ".join(keywords.split())
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    return [(result.entry_id, result.title, result.summary) for result in search.results()]
