"""Coleta RSS para fila editorial — comando opt-in, sem LLM e sem WordPress."""
import argparse
import json
import os
from datetime import datetime, timezone
from mkt_flow_p0.rss_ingestor import FEEDS_PADRAO, fetch_feed
from mkt_flow_p0.fila_pautas import registrar, listar
from mkt_flow_p0.opportunities import recent
from mkt_flow_p0.product_catalog import load as load_product_catalog, identify_in_headline


def coletar(fonte="", limite=5):
    if fonte and fonte not in FEEDS_PADRAO:
        raise ValueError("Fonte desconhecida")
    if os.getenv("CONEXO_REQUIRE_CLOUD_PERSISTENCE") == "1":
        if not all(os.getenv(k, "").strip() for k in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN")):
            raise RuntimeError("PERSISTENCIA_CLOUD_AUSENTE: coleta cancelada antes da rede")
    resultados = {"novas": 0, "duplicadas": 0, "falhas": [], "fora_da_janela": 0,
                  "catalogo": {"correspondencias": 0, "sem_correspondencia": 0, "revisao": 0}}
    try:
        catalogo = load_product_catalog()
    except (OSError, ValueError, KeyError, TypeError):
        catalogo = None  # catálogo auxiliar jamais interrompe a coleta editorial
        resultados["catalogo"]["indisponivel"] = True
    now = datetime.now(timezone.utc)
    for nome, feed_url in FEEDS_PADRAO.items():
        if fonte and nome != fonte:
            continue
        feed = fetch_feed(feed_url, fonte=nome, max_items=limite)
        if "erro" in feed:
            resultados["falhas"].append({"fonte": nome, "motivo": feed["erro"]})
            continue
        for item in feed["itens"][:limite]:
            if not recent(item.get("published"), now, 168):
                resultados["fora_da_janela"] += 1
                continue
            if catalogo is not None:
                try:
                    classification = identify_in_headline(item.get("titulo", ""), catalogo)
                    bucket = {"CANDIDATE_MATCH": "correspondencias",
                              "NO_MATCH": "sem_correspondencia",
                              "REVIEW": "revisao"}[classification["status"]]
                    resultados["catalogo"][bucket] += 1
                except (ValueError, KeyError, TypeError, AttributeError):
                    resultados["catalogo"]["revisao"] += 1
                    # Falha auxiliar nunca bloqueia a fila RSS.
            try:
                status = registrar(item)
                resultados["novas" if status["novo"] else "duplicadas"] += 1
            except (ValueError, RuntimeError, OSError) as exc:
                resultados["falhas"].append({"fonte": nome, "motivo": str(exc)})
    return resultados


def main():
    ap = argparse.ArgumentParser(description="Coleta RSS segura para fila editorial")
    ap.add_argument("--fonte", default="")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--listar", action="store_true")
    args = ap.parse_args()
    if not 1 <= args.limit <= 50:
        ap.error("--limit deve estar entre 1 e 50")
    try:
        result = {"pautas": listar(limite=args.limit)} if args.listar else coletar(args.fonte, args.limit)
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"erro": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))
    if result.get("falhas"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
