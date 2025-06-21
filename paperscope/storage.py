import json
import os
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
    """
    db = load_db()
    if not any(item["id"] == entry["id"] for item in db):
        db.append(entry)
        save_db(db)
