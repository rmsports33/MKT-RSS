#!/usr/bin/env python3
"""Convert the sourced Binance revision into a NEW private review-only handoff.

No Groq, Turso, WordPress writes, factual approval or secret handling.
The generated handoff has distinct identity/version and pending review flags.
"""
import argparse
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "docs/ARTIGO_BINANCE_REVISAO_2026-11-14.md"
BASE = Path.home() / ".local/share/conexo-os/handoffs"
SOURCE = "https://tecnoblog.net/noticias/r-34-bilhoes-binance-cobriu-100-do-prejuizo-do-maior-roubo-de-cripto-da-historia/"

# Publicly accessible, published ConexoTech articles verified 2026-11-14.
# These URLs are not factual endorsements and do not substitute for Gate review.
VERIFIED_RELATED_URLS = [
    "https://conexotech.com.br/binance-ataque-hacker-636-bilhoes-coreia-do-norte/",
    "https://conexotech.com.br/como-hackers-roubam-criptomoedas-carteiras-corretoras/",
    "https://conexotech.com.br/banco-central-99-incidentes-ciberneticos-financeiros-2026/",
]

SOURCES = [
    {"name": "Reuters 14/11", "url": "https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/",
     "facts": ["Em 14/11, Reuters atribuiu a Binance cobertura de 95% e indicou que as retiradas ainda eram reabertas progressivamente."]},
    {"name": "Reuters 31/10", "url": "https://www.fidelity.com/news/article/company-news/202610311134RTRSNEWSCOMBINED_L6N46H03L_1",
     "facts": ["Em 31/10, a empresa disse ter reposto 90% dos ativos desviados e buscar tokens de menor liquidez."]},
    {"name": "AP análise do ataque", "url": "https://apnews.com/article/550e9b876550f71f07098494fe735beb",
     "facts": ["A AP informou que o ataque atingiu aproximadamente US$ 6,36 bilhões, com congelamento de aproximadamente US$ 3 bilhões, segundo as informações disponíveis na época."]},
    {"name": "Tecnoblog 14/11", "url": SOURCE,
     "facts": ["Tecnoblog divulgou que a Binance anunciou cobrir 100% dos ativos afetados e publicou prova de reservas."]},
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-image', action='store_true')
    parser.add_argument('--editorial-review', action='store_true')
    args = parser.parse_args()
    from mkt_flow_p0.editorial_import import processar_artigo_importado
    if not ARTICLE.is_file():
        raise SystemExit("BLOCKED: reviewed Markdown absent from checkout")
    text = ARTICLE.read_text(encoding="utf-8")
    if not text.startswith("# ") or len(text.split()) < 200:
        raise SystemExit("BLOCKED: invalid article")
    title, _, body = text.partition("\n")
    title = title[2:].strip()
    # The reviewer notice must be part of the workflow, never part of the story.
    body = re.sub(r"\n> \*\*Estado editorial:\*\*.*\Z", "", body, flags=re.S).strip()
    # Keep original research material intact; produce a new immutable version.
    payload = {
        "source_url": SOURCE, "source_name": "Tecnoblog",
        "article": {
            "titulo_seo": title,
            "meta_description": "Binance anunciou cobertura integral após ataque de US$ 6,3 bi, mas Reuters cita 95%. Entenda a diferença entre repor saldos e recuperar ativos.",
            "slug": "binance-cobertura-roubo-cripto-2026-revisao",
            "texto_markdown": body,
        },
        "research": {"sources": SOURCES},
    }
    if args.editorial_review:
        from ops.hostinger.binance_editorial_review import enrich_review_payload
        payload = enrich_review_payload(payload)
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    image_manifest = None
    image_base = None
    if args.with_image:
        image_base = Path.home() / ".local/share/conexo-os/imagens/binance"
        manifest_path = image_base / "image-manifest.json"
        if not manifest_path.is_file():
            raise SystemExit("BLOCKED: reviewed image manifest missing; run --image-stage first")
        image_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        from mkt_flow_p0.image_protocol import validate_prepared_manifest
        validate_prepared_manifest(image_manifest, base_dir=image_base)
    target = BASE / ("binance-revisao-" + uuid.uuid4().hex[:12])
    report = processar_artigo_importado(
        payload, target, genero="noticia", offline=True,
        image_manifest=image_manifest, image_base=image_base,
        verified_related_urls=VERIFIED_RELATED_URLS if args.editorial_review else None)

    summary = {
        "status": "REVIEW_ONLY_IMPORT_CREATED",
        "path": str(target),
        "version_sha256": report.get("version_sha256"),
        "review_ready": report.get("article_complete_for_human_review"),
        "wordpress_written": report.get("wordpress_written"),
        "publication_authorized": report.get("publication_authorized"),
        "source_count": len(payload["research"]["sources"]),
        "research_claims": sum(len(s["facts"]) for s in SOURCES),
        "image_manifest_applied": bool(args.with_image),
        "assisted_editorial_review_applied": bool(args.editorial_review),
        "editorial_readiness_status": (report.get("readiness") or {}).get("status"),
        "substantive_review_status": (report.get("substantive_review") or {}).get("status"),
        "voice_application_status": (report.get("editorial_voice_application") or {}).get("status"),
        "preview_path": report.get("preview_path"),
        "image_research_status": (report.get("image_research") or {}).get("status"),
        "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
        # Derive blockers from the actual full report. Never carry over
        # hard-coded pre-review flags after a successful substantive critique.
        "pending": list(dict.fromkeys([
            *(report.get("readiness", {}).get("pendencias") or []),
            *([] if report.get("substantive_review", {}).get("status") == "PASS"
              else ["substantive_review"]),
            *([] if report.get("image_research", {}).get("status") == "PREPARED_LICENSED_IMAGE_INSTALLED"
              else ["image_package_not_prepared"]),
            "human_factual_approval",
            "authenticated_wordpress_gate_and_human_version_acceptance",
        ])),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
