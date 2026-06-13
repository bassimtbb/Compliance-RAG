from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg2
from psycopg2 import OperationalError
from psycopg2 import pool as pg_pool


@dataclass
class Hit:
    id: str
    text: str
    metadata: dict
    score: float


def _vec_to_pg(v) -> str:
    return f"[{','.join(str(float(x)) for x in v)}]"


class PgVectorStore:
    def __init__(self, dsn: str, minconn: int = 1, maxconn: int = 10):
        self._dsn = dsn
        self._pool = pg_pool.ThreadedConnectionPool(minconn, maxconn, dsn)

    @contextmanager
    def _cursor(self):
        conn = self._pool.getconn()
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                yield cur
            self._pool.putconn(conn)
        except OperationalError:
            self._pool.putconn(conn, close=True)
            raise
        except Exception:
            self._pool.putconn(conn)
            raise

    def ensure_collection(self, dim: int):
        with self._cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id text PRIMARY KEY,
                    text text,
                    metadata jsonb,
                    embedding vector({dim})
                );
            """)

    def ensure_index(self):
        with self._cursor() as cur:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS rag_chunks_embedding_hnsw_idx
                ON rag_chunks
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """)
        print("[store] ✅ Index HNSW (vector_cosine_ops) prêt sur rag_chunks")

    def upsert(self, ids, vectors, texts, metadatas):
        with self._cursor() as cur:
            for i, v, t, m in zip(ids, vectors, texts, metadatas):
                cur.execute("""
                    INSERT INTO rag_chunks (id, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text=EXCLUDED.text,
                        metadata=EXCLUDED.metadata,
                        embedding=EXCLUDED.embedding;
                """, (i, t, json.dumps(m), _vec_to_pg(v)))

    def search(self, query_vector, top_k: int = 5) -> list[Hit]:
        vec_str = _vec_to_pg(query_vector)
        with self._cursor() as cur:
            cur.execute("""
                WITH ranked AS (
                    SELECT id, text, metadata,
                           (embedding <=> %s::vector) AS distance
                    FROM rag_chunks
                )
                SELECT id, text, metadata, 1 - distance AS score
                FROM ranked
                ORDER BY distance ASC
                LIMIT %s;
            """, (vec_str, top_k))
            return [
                Hit(r[0], r[1],
                    r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                    float(r[3]))
                for r in cur.fetchall()
            ]
