from __future__ import annotations

import re

_COUNTS: dict[str, int] = {
    "email": 0,
    "telephone_fr": 0,
    "telephone_intl": 0,
    "nir": 0,
}

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

PHONE_FR_RE = re.compile(
    r"\b(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}\b"
)

PHONE_INTL_RE = re.compile(
    r"\+(?:32|34|39|41|44|49|31|45|46|47|48|30|36|351|352|353|354|358|420|421)"
    r"[\s.\-]?\d[\d\s.\-]{5,14}\b"
)

NIR_RE = re.compile(
    r"\b[12][\s\-]?\d{2}[\s\-]?"
    r"(?:0[1-9]|1[0-2])[\s\-]?"
    r"(?:\d{2}|2[AB])[\s\-]?"
    r"\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b"
)


def anonymize(text: str) -> str:
    global _COUNTS

    def _rep_email(m):
        _COUNTS["email"] += 1
        return "[EMAIL]"

    def _rep_phone_fr(m):
        _COUNTS["telephone_fr"] += 1
        return "[TELEPHONE]"

    def _rep_phone_intl(m):
        _COUNTS["telephone_intl"] += 1
        return "[TELEPHONE]"

    def _rep_nir(m):
        _COUNTS["nir"] += 1
        return "[NIR]"

    text = EMAIL_RE.sub(_rep_email, text)
    text = PHONE_FR_RE.sub(_rep_phone_fr, text)
    text = PHONE_INTL_RE.sub(_rep_phone_intl, text)
    text = NIR_RE.sub(_rep_nir, text)
    return text


def sanitize_query(text: str) -> tuple[str, bool]:
    had_pii = contains_pii(text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_FR_RE.sub("[TELEPHONE]", text)
    text = PHONE_INTL_RE.sub("[TELEPHONE]", text)
    text = NIR_RE.sub("[NIR]", text)
    return text, had_pii


def contains_pii(text: str) -> bool:
    return bool(
        EMAIL_RE.search(text)
        or PHONE_FR_RE.search(text)
        or PHONE_INTL_RE.search(text)
        or NIR_RE.search(text)
    )


def report() -> dict:
    return dict(_COUNTS)


def reset():
    _COUNTS["email"] = 0
    _COUNTS["telephone_fr"] = 0
    _COUNTS["telephone_intl"] = 0
    _COUNTS["nir"] = 0
