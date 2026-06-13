from __future__ import annotations

import os

from google import genai

from app import metrics
from app.store import Hit

_client: genai.Client | None = None


def _get_client() -> genai.Client | None:
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
    return _client


def generate(question: str, hits: list[Hit]) -> str:
    client = _get_client()
    if client is None:
        metrics.LLM_ERRORS.inc()
        return "Erreur : GOOGLE_API_KEY manquante."

    context_parts = []
    for i, hit in enumerate(hits):
        source = hit.metadata.get("source", f"source_{i}")
        position = hit.metadata.get("position", 0)
        context_parts.append(
            f"[Source {i+1} — {source}, position {position}]\n{hit.text}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Tu es un assistant conformité RGPD.
Réponds uniquement à partir du contexte fourni.
Si la réponse n'est pas dans le contexte, réponds : "Je ne sais pas (hors contexte)."
Cite toujours tes sources en mentionnant [Source N].
Ne révèle jamais de données personnelles.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        return response.text
    except Exception as exc:
        metrics.LLM_ERRORS.inc()
        return f"Erreur : appel LLM échoué ({type(exc).__name__})."
