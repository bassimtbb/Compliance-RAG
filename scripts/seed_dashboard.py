from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request

QUESTIONS_NORMAL = [
    "Quels sont les droits des personnes concernées selon le RGPD ?",
    "Qu'est-ce que le consentement au sens du RGPD ?",
    "Quelles sont les obligations du responsable de traitement ?",
    "Qu'est-ce qu'une violation de données personnelles ?",
    "Quel est le rôle du délégué à la protection des données (DPO) ?",
    "Quelles sont les sanctions prévues en cas de non-conformité au RGPD ?",
    "Qu'est-ce que le principe de minimisation des données ?",
    "Comment exercer son droit à l'effacement ?",
    "Qu'est-ce qu'une analyse d'impact relative à la protection des données (AIPD) ?",
    "Quelles sont les bases légales d'un traitement de données personnelles ?",
]

QUESTIONS_PII = [
    "Mon email est jean.dupont@example.com, est-ce que le RGPD protège cette donnée ?",
    "Vous pouvez me contacter au 06 12 34 56 78 pour plus d'informations sur le RGPD ?",
    "Mon numéro de sécurité sociale est 1 85 01 75 123 456 78, dois-je le communiquer à mon employeur ?",
    "Pouvez-vous écrire à marie.martin@société.fr pour confirmer ma demande d'effacement ?",
]

QUESTIONS_OFFTOPIC = [
    "Quelle est la recette de la tarte tatin ?",
    "Qui a gagné la coupe du monde de football en 2018 ?",
    "Quel temps fait-il à Paris demain ?",
    "Donne-moi un itinéraire pour aller de Lyon à Marseille.",
]


def build_pool(weights: dict[str, int]) -> list[str]:
    pool: list[str] = []
    for question in QUESTIONS_NORMAL:
        pool.extend([question] * weights["normal"])
    for question in QUESTIONS_PII:
        pool.extend([question] * weights["pii"])
    for question in QUESTIONS_OFFTOPIC:
        pool.extend([question] * weights["offtopic"])
    return pool


def ask(base_url: str, question: str, top_k: int, timeout: float) -> dict:
    payload = json.dumps({"question": question, "top_k": top_k}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description="Envoie un trafic varié vers /ask pour peupler les métriques "
                     "Prometheus et le dashboard Grafana avant une capture d'écran."
    )
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL de l'API")
    parser.add_argument("--count", type=int, default=60, help="Nombre de requêtes à envoyer")
    parser.add_argument("--delay", type=float, default=1.0, help="Délai moyen entre requêtes (s)")
    parser.add_argument("--jitter", type=float, default=0.5, help="Variation aléatoire +/- du délai (s)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout HTTP par requête (s)")
    parser.add_argument("--seed", type=int, default=None, help="Seed aléatoire (reproductibilité)")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    pool = build_pool({"normal": 6, "pii": 2, "offtopic": 1})

    ok, errors = 0, 0
    for i in range(1, args.count + 1):
        question = random.choice(pool)
        top_k = random.randint(1, 10)

        try:
            result = ask(args.url, question, top_k, args.timeout)
            ok += 1
            print(
                f"[{i}/{args.count}] OK  "
                f"latency={result.get('latency_ms')}ms "
                f"hits={len(result.get('sources', []))} "
                f"q={question[:60]!r}"
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            errors += 1
            print(f"[{i}/{args.count}] ERREUR {exc} — q={question[:60]!r}")

        if i < args.count:
            delay = max(0.0, args.delay + random.uniform(-args.jitter, args.jitter))
            time.sleep(delay)

    print(f"\nTerminé : {ok} OK, {errors} erreurs.")
    print("Attends ~1 min puis ouvre Grafana (http://localhost:3000) "
          "pour laisser les fenêtres rate()/histogram_quantile() se peupler.")


if __name__ == "__main__":
    main()
