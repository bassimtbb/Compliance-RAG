from __future__ import annotations

import re
import time

from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_client import make_asgi_app

from app import metrics
from app.pii import sanitize_query
from app.retrieve import retrieve
from app.generate import generate

app = FastAPI(title="Compliance RAG")
app.mount("/metrics", make_asgi_app())

REFUSAL_RE = re.compile(r"hors[\s\-]?contexte", re.IGNORECASE)


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    latency_ms: float


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    metrics.REQS.inc()
    start = time.time()

    clean_question, had_pii = sanitize_query(req.question)
    if had_pii:
        metrics.PII_QUERIES.inc()

    with metrics.LAT.time():
        hits = retrieve(clean_question, top_k=req.top_k)
        answer = generate(clean_question, hits)

    latency_ms = (time.time() - start) * 1000

    if REFUSAL_RE.search(answer):
        metrics.REFUSALS.inc()

    if hits:
        metrics.TOP1_SCORE.observe(hits[0].score)
    metrics.HITS_RETURNED.observe(len(hits))

    sources = [
        {
            "source": h.metadata.get("source", ""),
            "position": h.metadata.get("position", 0),
            "score": round(h.score, 3),
        }
        for h in hits
    ]

    return AskResponse(
        answer=answer,
        sources=sources,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/health")
def health():
    return {"status": "ok"}