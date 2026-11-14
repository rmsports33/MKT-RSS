#!/usr/bin/env python3
"""Convert the sourced Binance revision into a NEW private review-only handoff.

No Groq, Turso, WordPress writes, factual approval or secret handling.
The generated handoff has distinct identity/version and pending review flags.
"""
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

SOURCES = [
    {"name": "Reuters 14/11", "url": "https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/",
     "facts": ["Em 14/11, Reuters atribuiu a Binance cobertura de 95% e indicou que as retiradas ainda eram reabertas progressivamente."]},
    {"name": "Reuters 31/10", "url": "https://www.fidelity.com/news/article/company-news/202610311134RTRSNEWSCOMBINED_L6N46H03L_1",
     "facts": ["Em 31/10, a empresa disse ter reposto 90% dos ativos desviados e buscar tokens de menor liquidez."]},
    {"name": "AP ataque", "url": "https://apnews.com/article/39cda8ceb8095e036334a18549d3d20d",
     "facts": ["A Binance investigou comprometimento de equipamento ligado ao setor DevOps, informou suspensão de retiradas e disse que trabalhava com autoridades."]},
    {"name": "Tecnoblog 14/11", "url": SOURCE,
     "facts": ["Tecnoblog divulgou que a Binance anunciou cobrir 100% dos ativos afetados e publicou prova de reservas."]},
]

def main():
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
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = BASE / ("binance-revisao-" + uuid.uuid4().hex[:12])
    report = processar_artigo_importado(payload, target, genero="noticia", offline=True)
    summary = {
        "status": "REVIEW_ONLY_IMPORT_CREATED",
        "path": str(target),
        "version_sha256": report.get("version_sha256"),
        "review_ready": report.get("article_complete_for_human_review"),
        "wordpress_written": report.get("wordpress_written"),
        "publication_authorized": report.get("publication_authorized"),
        "source_count": len(payload["research"]["sources"]),
        "research_claims": sum(len(s["facts"]) for s in SOURCES),
        "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "pending": ["substantive_review", "image_licensed_and_visual_review", "human_factual_approval"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
