import json
import os
from datetime import datetime
from paperscope.config import DB_PATH

def load_db():
    """
    Load the local database of papers (stored as JSON).
    """
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return []

def save_db(data):
    """
    Save the database to disk.
    """
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_entry(entry):
    """
    Add a new paper summary entry if it doesn't already exist.
    Automatically adds timestamp if not present.
    """
    db = load_db()
    
    # Add timestamp if not present
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().isoformat()
    
    if not any(item["id"] == entry["id"] for item in db):
        db.append(entry)
        save_db(db)
        return True
    return False

def get_history(limit=None):
    """
    Get all papers sorted by timestamp (newest first).
    """
    db = load_db()
    # Sort by timestamp if available, newest first
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
    
    # Filter out the paper with the matching ID
    db = [item for item in db if item.get("id") != paper_id]
    
    if len(db) < original_length:
        save_db(db)
        return True
    return False
