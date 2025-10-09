import json
import os
from typing import Tuple

from paperscope.storage import save_db
from paperscope.summarizer_demo import summarize


def load_demo_data(build_index: bool = False) -> tuple[bool,str]:
    """Create a small demo database and metadata file.

    If build_index is True, attempt to call the repository's build_index function.
    Returns True.
    """
    sample = [
        {
            "id": "demo:1",
            "title": "Demonstration of PaperScope",
            "abstract": "This paper demonstrates the PaperScope demo flow and UI.",
            "summary": summarize("This paper demonstrates the PaperScope demo flow and UI.")
        },
        {
            "id": "demo:2",
            "title": "Sample Paper on Robot Learning",
            "abstract": "An example abstract about robot learning and reinforcement learning.",
            "summary": summarize("An example abstract about robot learning and reinforcement learning.")
        }
    ]

    try:
        save_db(sample)
    except Exception as e:
        return False, f"Failed to save demo DB: {e}"

    # Write meta.json for FAISS metadata fallback
    try:
        with open("meta.json", "w") as f:
            json.dump(sample, f)
    except Exception as e:
        return False, f"Failed to write meta.json: {e}"

    if build_index:
        try:
            # Import lazily because vector_store may require faiss
            from paperscope.vector_store import build_index as _build

            _build()
            return True, "Demo DB and FAISS index created."
        except Exception as e:
            # Index build failed or faiss missing; still OK for demo but warn
            return True, f"Demo DB created; FAISS index build skipped/failed: {e}"

    return True, "Demo DB created"
