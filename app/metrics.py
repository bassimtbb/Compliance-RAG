from __future__ import annotations

from prometheus_client import Counter, Histogram

REQS = Counter(
    "rag_requests_total",
    "Nombre total de requêtes reçues sur POST /ask.",
)

REFUSALS = Counter(
    "rag_refusals_total",
    "Nombre de réponses 'hors contexte' émises par le LLM.",
)

LLM_ERRORS = Counter(
    "rag_llm_errors_total",
    "Nombre d'erreurs lors des appels à l'API Gemini.",
)

PII_QUERIES = Counter(
    "rag_pii_queries_total",
    "Nombre de questions utilisateur contenant des données personnelles détectées avant anonymisation.",
)

LAT = Histogram(
    "rag_latency_seconds",
    "Latence totale de la requête /ask : sanitize + embed + pgvector + LLM.",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

EMBED_LAT = Histogram(
    "rag_embed_duration_seconds",
    "Durée de l'encodage de la question par SentenceTransformer (all-MiniLM-L6-v2).",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

DB_LAT = Histogram(
    "rag_db_query_duration_seconds",
    "Durée de la recherche vectorielle ANN (HNSW) sur pgvector.",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)

TOP1_SCORE = Histogram(
    "rag_top1_score",
    "Score de similarité cosinus du chunk le mieux classé (0=orthogonal, 1=identique).",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
)

HITS_RETURNED = Histogram(
    "rag_hits_returned",
    "Nombre de chunks retournés par la recherche vectorielle.",
    buckets=[1, 2, 3, 5, 10, 20],
)
