from __future__ import annotations

import os

import google.generativeai as genai

from app.store import Hit
 
def generate(question: str, hits: list[Hit]) -> str:

    api_key = os.environ.get("GOOGLE_API_KEY", "")

    if not api_key:

        return "Erreur : GOOGLE_API_KEY manquante."
 
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")
 
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
 
    response = model.generate_content(prompt)

    return response.text
 