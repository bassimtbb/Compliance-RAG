"""Filtrage PII — emails, téléphones, noms."""
import re
from dataclasses import dataclass, field

_COUNTS: dict[str, int] = {"email": 0, "telephone": 0}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b")

def anonymize(text: str) -> str:
    global _COUNTS
    def rep_email(m):
        _COUNTS["email"] += 1
        return "[EMAIL]"
    def rep_phone(m):
        _COUNTS["telephone"] += 1
        return "[TELEPHONE]"
    text = EMAIL_RE.sub(rep_email, text)
    text = PHONE_RE.sub(rep_phone, text)
    return text

def report() -> dict:
    return dict(_COUNTS)

def contains_pii(text: str) -> bool:
    return bool(EMAIL_RE.search(text) or PHONE_RE.search(text))

def reset():
    _COUNTS["email"] = 0
    _COUNTS["telephone"] = 0