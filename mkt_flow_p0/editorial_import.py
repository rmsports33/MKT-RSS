"""Import a researched article into the existing MKT-RSS editorial handoff.

No RSS fetching, LLM calls, WordPress writes or publication. The original RSS
pipeline remains the complete authoring engine when its runtime is available.
"""
import argparse
import json
from pathlib import Path

from mkt_flow_p0.editorial_identity import (
    criar_handoff_chatgpt, salvar_handoff_chatgpt, validar_handoff_chatgpt,
)


def importar_artigo_para_handoff(payload, output_dir):
    """Import a ChatGPT/researcher article; claims stay PENDING_HUMAN_REVIEW."""
    if not isinstance(payload, dict) or set(payload) != {
            "source_url", "source_name", "article", "research"}:
        raise ValueError("pacote exige source_url, source_name, article e research")
    source_name = payload["source_name"]
    if not isinstance(source_name, str) or not source_name.strip() or len(source_name) > 120:
        raise ValueError("nome da fonte original invalido")
    article = payload["article"]
    required = {"titulo_seo", "meta_description", "slug", "texto_markdown"}
    if not isinstance(article, dict) or set(article) != required:
        raise ValueError("campos do artigo invalidos")
    if (not isinstance(article["texto_markdown"], str)
            or len(article["texto_markdown"].split()) < 200):
        raise ValueError("artigo precisa de ao menos 200 palavras")
    handoff = criar_handoff_chatgpt(
        article, url_fonte=payload["source_url"],
        fonte_nome=source_name, contexto_complementar=payload["research"])
    path = salvar_handoff_chatgpt(handoff, output_dir)
    return {**validar_handoff_chatgpt(handoff), "handoff_path": path,
            "wordpress_written": False, "provider_called": False}


def main():
    """Offline CLI: import a finished article; never call a model or WordPress."""
    parser = argparse.ArgumentParser(description="Importar artigo para revisao MKT-RSS")
    parser.add_argument("--import-article", type=Path, required=True)
    parser.add_argument("--handoff-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.import_article.stat().st_size > 1024 * 1024:
        parser.error("arquivo excede 1 MiB")
    payload = json.loads(args.import_article.read_text(encoding="utf-8"))
    report = importar_artigo_para_handoff(payload, args.handoff_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
