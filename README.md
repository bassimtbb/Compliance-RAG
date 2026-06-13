# Compliance RAG

Pipeline RAG (Retrieval-Augmented Generation) conforme RGPD, basé sur pgvector, avec filtrage des données personnelles (PII) et supervision Prometheus/Grafana.

## Démarrage rapide

```bash
git clone https://github.com/bassimtbb/Compliance-RAG.git
cd Compliance-RAG
cp .env.example .env
# Éditer .env et ajouter votre GOOGLE_API_KEY
docker compose up
```

Au premier lancement, `docker compose` exécute dans l'ordre :
1. **postgres** — démarrage de PostgreSQL + extension pgvector
2. **ingest** — extraction, anonymisation et découpage des documents de `corpus/`
3. **embed** — génération des embeddings et indexation dans pgvector
4. **api** — démarrage de l'API FastAPI sur `http://localhost:8000`
5. **prometheus** et **grafana** — supervision

## Tester le RAG

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelles sont les obligations RGPD ?"}'
```

La réponse contient le texte généré, les sources citées (document + position du chunk) et la latence de la requête.

## Architecture

```mermaid
flowchart LR
    DOC[Document<br/>PDF / HTML] --> ING[ingest.py]
    ING --> PII[pii.py<br/>Filtrage PII]
    PII --> EMB[embed.py<br/>all-MiniLM-L6-v2]
    EMB --> PGV[(pgvector)]
    PGV --> RET[retrieve.py<br/>top-k search]
    RET --> GEN[generate.py<br/>Gemini 2.5 Flash Lite]
    GEN --> API[api.py<br/>POST /ask]

    API -. /metrics .-> PROM[Prometheus]
    PROM --> GRAF[Grafana]
```

## Structure du projet

```
app/
├── pii.py          # Détection et masquage des PII (emails, téléphones, NIR)
├── ingest.py       # Extraction PDF/HTML + découpage en chunks + anonymisation
├── embed.py        # Génération des embeddings + upsert dans pgvector
├── store.py        # Adaptateur PgVectorStore (distance cosinus)
├── retrieve.py     # Recherche vectorielle top-k
├── generate.py     # Génération LLM (Gemini) + citation des sources
├── api.py          # API FastAPI : POST /ask + endpoint /metrics
└── metrics.py      # Métriques Prometheus

monitoring/
└── prometheus.yml  # Configuration du scraping Prometheus

corpus/
└── seed/           # Documents source versionnés (HTML + PDF RGPD)

docs/
└── COMPTE-RENDU.md # Rapport du projet
```

## Variables d'environnement

Copier `.env.example` vers `.env` et compléter les valeurs :

```bash
GOOGLE_API_KEY=your_key_here
DATABASE_URL=postgresql://rag:rag@postgres:5432/rag
```

> Le fichier `.env` est ignoré par Git (`.gitignore`) — ne jamais y committer de secrets.

## Services

| Service | Port | Description |
|---|---|---|
| API | 8000 | Endpoint `POST /ask` |
| Postgres + pgvector | 5432 | Base vectorielle |
| Prometheus | 9090 | Collecte des métriques |
| Grafana | 3000 | Dashboard (`admin` / `admin`) |

## Licences du corpus

- **Texte officiel du RGPD** (Règlement UE 2016/679) — domaine public
- **RGPD1.pdf** — rapport CGE 2019 — domaine public
- **Fichiers HTML de `corpus/seed/`** — corpus interne de formation

## Équipe

- **Bassim Tabbeb** — R1 Données/Conformité + R2 Embeddings/Indexation
- **Mathis Penagos** — R3 Retrieval/LLM + R4 DevOps/Monitoring
