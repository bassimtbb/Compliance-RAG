

from __future__ import annotations

import time

from fastapi import FastAPI

from pydantic import BaseModel

from prometheus_client import Counter, Histogram, make_asgi_app

from app.retrieve import retrieve

from app.generate import generate
 
app = FastAPI(title="Compliance RAG")
 
REQS = Counter("rag_requests_total", "Nombre de requêtes /ask")

LAT = Histogram("rag_latency_seconds", "Latence des réponses")

REFUSALS = Counter("rag_refusals_total", "Nombre de refus")
 
app.mount("/metrics", make_asgi_app())
 
class AskRequest(BaseModel):

    question: str

    top_k: int = 5
 
class AskResponse(BaseModel):

    answer: str

    sources: list[dict]

    latency_ms: float
 
@app.post("/ask", response_model=AskResponse)

def ask(req: AskRequest):

    REQS.inc()

    start = time.time()

    with LAT.time():

        hits = retrieve(req.question, top_k=req.top_k)

        answer = generate(req.question, hits)

    latency_ms = (time.time() - start) * 1000
 
    if "hors contexte" in answer.lower():

        REFUSALS.inc()
 
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

        latency_ms=round(latency_ms, 2)

    )
 
@app.get("/health")

def health():

    return {"status": "ok"}
 