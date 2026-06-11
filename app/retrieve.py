from __future__ import annotations
import os
from sentence_transformers import SentenceTransformer
from app.store import PgVectorStore, Hit
 
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None
_store = None
 
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model
 
def get_store():
    global _store
    if _store is None:
        dsn = os.environ.get("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag")
        _store = PgVectorStore(dsn)
    return _store
 
def retrieve(question: str, top_k: int = 5) -> list[Hit]:
    model = get_model()
    store = get_store()
    vector = model.encode(question)
    hits = store.search(vector, top_k=top_k)
    return hits