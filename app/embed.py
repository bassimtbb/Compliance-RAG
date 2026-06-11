"""Embeddings + upsert dans pgvector."""
from __future__ import annotations
import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.store import PgVectorStore

CHUNKS = Path("corpus/chunks.jsonl")
MODEL_NAME = "all-MiniLM-L6-v2"


def embed():
    dsn = os.environ.get("DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag")
    model = SentenceTransformer(MODEL_NAME)
    store = PgVectorStore(dsn)
    store.ensure_collection(dim=384)

    records = [json.loads(l) for l in CHUNKS.read_text().splitlines() if l.strip()]
    texts = [r["text"] for r in records]

    print(f"[embed] {len(texts)} chunks → embeddings {MODEL_NAME}...")
    vectors = model.encode(texts, show_progress_bar=True, batch_size=32)

    store.upsert(
        ids=[r["id"] for r in records],
        vectors=vectors,
        texts=texts,
        metadatas=[r["metadata"] for r in records],
    )
    print(f"[embed] ✅ {len(records)} chunks indexés dans pgvector")


if __name__ == "__main__":
    embed()