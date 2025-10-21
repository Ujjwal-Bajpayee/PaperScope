import json
import os
from datetime import datetime
from paperscope.config import DB_PATH


def load_db():
    """
    Load the local database of papers (stored as JSON).
    """
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_db(data):
    """
    Save the database to disk.
    """
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_entry(entry):
    """
    Add a new paper summary entry if it doesn't already exist.
    Automatically adds timestamp if not present.
    """
    db = load_db()

    # Add timestamp if not present
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().isoformat()

    # Check for duplicates by ID
    if not any(item.get("id") == entry.get("id") for item in db):
        db.append(entry)
        save_db(db)
        return True
    return False


def get_history(limit=None):
    """
    Get all papers sorted by timestamp (newest first).
    """
    db = load_db()
    sorted_db = sorted(db, key=lambda x: x.get("timestamp", ""), reverse=True)

    if limit:
        return sorted_db[:limit]
    return sorted_db


def clear_history():
    """
    Clear all stored papers from the database.
    """
    save_db([])
    return True


def delete_entry(paper_id):
    """
    Delete a specific paper entry by its ID.
    Returns True if deleted, False if not found.
    """
    db = load_db()
    original_length = len(db)

    db = [item for item in db if item.get("id") != paper_id]

    if len(db) < original_length:
        save_db(db)
        return True
    return False


# ✅ New helper function added for streamlit_app.py compatibility
def save_history_entry(paper_id, title, summary, source="uploaded_pdf"):
    """
    Save a new summary entry into the history file.

    Args:
        paper_id (str): Unique identifier (e.g., file name or arxiv id)
        title (str): Paper title or filename
        summary (str): The summarized text
        source (str): Either 'arxiv', 'uploaded_pdf', or 'manual'
    """
    entry = {
        "id": paper_id,
        "title": title,
        "summary": summary,
        "source": source,
        "timestamp": datetime.now().isoformat()
    }

    db = load_db()

    # Avoid duplicate entries
    existing_ids = [item.get("id") for item in db]
    if paper_id not in existing_ids:
        db.append(entry)
        save_db(db)
        return True

    return False
