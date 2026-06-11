"""Vector store pgvector (Postgres)."""
from __future__ import annotations
import json
from dataclasses import dataclass
import psycopg2


@dataclass
class Hit:
    id: str
    text: str
    metadata: dict
    score: float


class PgVectorStore:
    def __init__(self, dsn: str):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True

    def ensure_collection(self, dim: int):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id text PRIMARY KEY,
                    text text,
                    metadata jsonb,
                    embedding vector({dim})
                );
            """)

    def upsert(self, ids, vectors, texts, metadatas):
        with self.conn.cursor() as cur:
            for i, v, t, m in zip(ids, vectors, texts, metadatas):
                cur.execute("""
                    INSERT INTO rag_chunks (id, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text=EXCLUDED.text,
                        metadata=EXCLUDED.metadata,
                        embedding=EXCLUDED.embedding;
                """, (i, t, json.dumps(m), str(v.tolist())))

    def search(self, query_vector, top_k: int = 5) -> list[Hit]:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, text, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM rag_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (str(query_vector.tolist()), str(query_vector.tolist()), top_k))
            return [
                Hit(r[0], r[1],
                    r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                    float(r[3]))
                for r in cur.fetchall()
            ]