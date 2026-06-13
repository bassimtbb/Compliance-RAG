from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

import pdfplumber
from trafilatura import extract

from app.pii import anonymize, report, reset

CORPUS = Path("corpus")
OUT = Path("corpus/chunks.jsonl")


def extract_pdf(path: Path) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
    return "\n".join(parts)


def extract_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return extract(raw) or ""


def extract_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _split_long_paragraph(para: str, max_chars: int) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
    pieces, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_chars and current:
            pieces.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        pieces.append(current.strip())
    final = []
    for piece in pieces:
        if len(piece) > max_chars:
            final.extend(
                piece[i:i + max_chars] for i in range(0, len(piece), max_chars)
            )
        else:
            final.append(piece)
    return final


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(para) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_paragraph(para, max_chars))
        elif len(current) + len(para) > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]


def ingest():
    reset()
    OUT.parent.mkdir(exist_ok=True)
    records = []

    files = (
        list(CORPUS.rglob("*.pdf"))
        + list(CORPUS.rglob("*.html"))
        + list(CORPUS.rglob("*.txt"))
        + list(CORPUS.rglob("*.md"))
    )

    files = [f for f in files if "raw" not in f.parts]

    for filepath in files:
        try:
            if filepath.suffix == ".pdf":
                text = extract_pdf(filepath)
            elif filepath.suffix == ".html":
                text = extract_html(filepath)
            else:
                text = extract_text(filepath)

            if not text.strip():
                print(f"[SKIP] {filepath.name} — texte vide")
                continue

            for i, chunk in enumerate(chunk_text(text)):
                clean = anonymize(chunk)
                records.append({
                    "id": hashlib.sha256(
                        f"{filepath.name}_{i}".encode()
                    ).hexdigest()[:16],
                    "text": clean,
                    "metadata": {
                        "source": filepath.name,
                        "position": i,
                        "doc_id": filepath.stem,
                    }
                })
        except Exception as e:
            print(f"[WARN] {filepath.name} : {e}")

    with OUT.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    pii_report = report()
    print(f"[anonymisation] {len(records)} chunks traités")
    print(f"  - emails masqués          : {pii_report.get('email', 0)}")
    print(f"  - téléphones FR masqués   : {pii_report.get('telephone_fr', 0)}")
    print(f"  - téléphones INTL masqués : {pii_report.get('telephone_intl', 0)}")
    print(f"  - NIR masqués (Art.9)     : {pii_report.get('nir', 0)}")
    return records


if __name__ == "__main__":
    ingest()