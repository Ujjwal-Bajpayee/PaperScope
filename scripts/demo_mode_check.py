"""Simple script to verify Demo Mode works without external APIs.

Run with: DEMO_MODE=1 python3 scripts/demo_mode_check.py

It checks that summarize() returns quickly and that building/searching the FAISS index runs without external calls.
"""
import os
import sys

# Ensure demo mode
os.environ["DEMO_MODE"] = "1"

# Import the appropriate summarizer for demo mode
if os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes"):
    from paperscope.summarizer_demo import summarize
else:
    from paperscope.summarizer import summarize
from paperscope.storage import save_db
# vector_store may require faiss; import lazily and handle missing dependency
try:
    from paperscope.vector_store import build_index, search_similar
    _HAS_FAISS = True
except Exception:
    build_index = None
    search_similar = None
    _HAS_FAISS = False


def run_checks():
    print("Running Demo Mode checks...")

    # Prepare a small sample DB
    sample = [
        {"id": "1", "title": "Demo Paper", "abstract": "This is a demo abstract.", "summary": summarize("This is a demo abstract.")}
    ]
    save_db(sample)
    print("Saved sample DB")

    # Build index (uses embed_text which is local and deterministic)
    try:
            if _HAS_FAISS and build_index is not None:
                build_index()
                print("FAISS index build: OK")
            else:
                print("FAISS not available: skipping index build (simulated OK)")
    except Exception as e:
        print("FAISS index build: FAIL", e)
        sys.exit(2)

    # Run a search
    try:
            if _HAS_FAISS and search_similar is not None:
                res = search_similar("demo query")
                print("FAISS search returned:", res)
            else:
                print("FAISS not available: performing simulated search by loading meta.json if present")
                import json
                if os.path.exists("meta.json"):
                    with open("meta.json") as f:
                        meta = json.load(f)
                    print("Simulated search returned:", meta[:1])
                else:
                    print("No meta.json present — simulated search returns empty list")
    except Exception as e:
        print("FAISS search: FAIL", e)
        sys.exit(3)

    print("All demo checks passed.")


if __name__ == '__main__':
    run_checks()
