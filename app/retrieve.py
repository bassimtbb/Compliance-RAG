from __future__ import annotations

import os

from sentence_transformers import SentenceTransformer

from app import metrics
from app.store import Hit, PgVectorStore

MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None
_store: PgVectorStore | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_store() -> PgVectorStore:
    global _store
    if _store is None:
        dsn = os.environ.get("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag")
        _store = PgVectorStore(dsn)
    return _store


def retrieve(question: str, top_k: int = 5) -> list[Hit]:
    model = get_model()
    store = get_store()

    with metrics.EMBED_LAT.time():
        vector = model.encode(question)

    with metrics.DB_LAT.time():
        hits = store.search(vector, top_k=top_k)

    return hits
