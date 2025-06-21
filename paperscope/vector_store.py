import faiss
import numpy as np
import json
import os
from paperscope.summarizer import summarize
from paperscope.storage import load_db, save_db
from paperscope.config import DB_PATH

VECTOR_INDEX_PATH = "faiss.index"
VECTOR_DIM = 768  


def embed_text(text):
    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.rand(VECTOR_DIM).astype("float32")

def build_index():
    """
    Build FAISS index from summaries in the local database.
    """
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
    if not os.path.exists(VECTOR_INDEX_PATH):
        return []

    index = faiss.read_index(VECTOR_INDEX_PATH)
    query_vec = embed_text(text).reshape(1, -1)
    D, I = index.search(query_vec, k)
    with open("meta.json") as f:
        metadata = json.load(f)
    return [metadata[i] for i in I[0] if i < len(metadata)]
