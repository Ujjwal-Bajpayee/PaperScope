import json
import os
from paperscope.storage import load_db, save_db
from paperscope.config import DB_PATH

# Try to import optional dependencies
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    _HAS_FAISS = True
except ImportError:
    _HAS_FAISS = False
    # Create dummy classes for when dependencies are missing
    class DummyModel:
        def encode(self, text):
            return [0.1] * 768  # Dummy embedding
    SentenceTransformer = lambda x: DummyModel()
    np = None
    faiss = None

VECTOR_INDEX_PATH = "faiss.index"
VECTOR_DIM = 768  


def embed_text(text):
    """
    Returns a text embedding.
    Uses real model if available, otherwise falls back to a mock embedding.
    """
    if not _HAS_FAISS:
        # Return a simple hash-based embedding for demo mode
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        return [float((hash_val >> i) & 1) for i in range(VECTOR_DIM)]
    
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(text).astype("float32")
    except:
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.rand(VECTOR_DIM).astype("float32")


def build_index():
    """
    Build FAISS index from summaries in the local database.
    """
    if not _HAS_FAISS:
        # In demo mode, just save metadata
        db = load_db()
        with open("meta.json", "w") as f:
            json.dump(db, f)
        return
    
    db = load_db()
    vectors = []
    metadata = []
    for item in db:
        embedding = embed_text(item['summary'])
        vectors.append(embedding)
        metadata.append(item)
    if not vectors:
        return
    index = faiss.IndexFlatL2(VECTOR_DIM)
    index.add(np.array(vectors))
    faiss.write_index(index, VECTOR_INDEX_PATH)
    with open("meta.json", "w") as f:
        json.dump(metadata, f)

def search_similar(text, k=5):
    """
    Perform vector similarity search using FAISS.
    """
    if not _HAS_FAISS:
        # In demo mode, return simple keyword-based results
        if not os.path.exists("meta.json"):
            return []
        with open("meta.json") as f:
            metadata = json.load(f)
        # Simple keyword matching for demo
        results = []
        text_lower = text.lower()
        for item in metadata:
            if any(word in item.get('summary', '').lower() or word in item.get('title', '').lower() 
                   for word in text_lower.split()):
                results.append(item)
        return results[:k]
    
    if not os.path.exists(VECTOR_INDEX_PATH):
        return []

    index = faiss.read_index(VECTOR_INDEX_PATH)
    query_vec = embed_text(text).reshape(1, -1)
    D, I = index.search(query_vec, k)
    with open("meta.json") as f:
        metadata = json.load(f)
    return [metadata[i] for i in I[0] if i < len(metadata)]

