"""Seal already generated complete articles for blinded human review, locally.

No AI calls, no external service, no editor approvals. The reviewer receives
the blind file ONLY. The mapping and hashes are stored in a DIFFERENT private
directory; never commit or share the mapping with the reviewer.
"""
import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path

from scripts.prepare_mda_ab import _write_private


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def seal_pair(manifest, control_article, mda_article, blind_dir, private_key_dir, *, coin=None):
    if (not isinstance(manifest, dict)
            or manifest.get("schema") != "conexo-mda-ab-preflight/1"
            or manifest.get("only_delta") != "mda_voice_guidance"
            or manifest.get("provider_called") is not False
            or manifest.get("publication_authorized") is not False):
        raise ValueError("preflight inválido")
    if (not isinstance(control_article, str) or not isinstance(mda_article, str)
            or len(control_article.strip()) < 400 or len(mda_article.strip()) < 400
            or control_article == mda_article):
        raise ValueError("faltam dois textos distintos e completos para revisão")
    if coin is None:
        coin = secrets.randbelow(2)
    if coin not in (0, 1) or type(coin) is not int:
        raise ValueError("sorteio inválido")
    blind_path, key_path = Path(blind_dir).resolve(), Path(private_key_dir).resolve()
    if blind_path == key_path or blind_path in key_path.parents or key_path in blind_path.parents:
        raise ValueError("chave privada não pode ficar dentro da pasta cega")
    first, second = (control_article, mda_article) if coin == 0 else (mda_article, control_article)
    mapping = {"A": "control", "B": "mda"} if coin == 0 else {"A": "mda", "B": "control"}
    blind = (
        "CONEXOTECH — AVALIAÇÃO HUMANA CEGA A/B\n"
        "Textos completos. Não compartilhe a identidade dos braços até concluir e datar os pareceres.\n"
        "Notas 0–4 para necessidade do leitor, recorte, contribuição, voz e limites das fontes. "
        "Em cada critério: evidência curta e justificativa. "
        "Conferir fatos nas fontes; anotar regressões, lacunas e trechos redundantes. "
        "A avaliação não publica nem libera os textos no WordPress.\n\n"
        "======== TEXTO A ========\n" + first + "\n\n"
        "======== TEXTO B ========\n" + second + "\n\n"
        "======== PARECER INDEPENDENTE — PREENCHIMENTO HUMANO ========\n"
        "A: necessidade __/4, recorte __/4, contribuição __/4, voz __/4, fontes __/4\n"
        "B: necessidade __/4, recorte __/4, contribuição __/4, voz __/4, fontes __/4\n"
        "Fatos, correções e limitações verificadas: ___________________\n"
        "Comparação explicada por trecho: _____________________________\n"
        "Decisão (A / B / empate / ambos reprovados): ________________\n"
        "Revisor independente / data: _______________________________\n"
    )
    key = {
        "schema": "conexo-mda-ab-private-key/1",
        "case_id": manifest["case_id"], "mapping": mapping,
        "source_sha256": manifest["source_sha256"],
        "brief_sha256": manifest["brief_sha256"],
        "intended_generation": manifest["intended_generation"],
        "control_prompt_sha256": manifest["control_prompt_sha256"],
        "mda_prompt_sha256": manifest["mda_prompt_sha256"],
        "control_article_sha256": _digest(control_article),
        "mda_article_sha256": _digest(mda_article),
        "model_execution_and_inputs_independently_verified": False,
        "human_independent_review_completed": False,
        "quality_improvement_demonstrated": False,
        "factual_approval": False,
        "publication_authorized": False,
    }
    blind_path.mkdir(mode=0o700, parents=True, exist_ok=False)
    key_path.mkdir(mode=0o700, parents=True, exist_ok=False)
    _write_private(blind_path / "review_A_B.md", blind)
    _write_private(key_path / "mapping.private.json",
                   json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    return {"case_id": manifest["case_id"],
            "blind_packet_created": True, "private_mapping_created_separately": True,
            "model_execution_verified": False, "human_review_completed": False,
            "publication_authorized": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Seal a completed MDA A/B pair, no web or AI")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--control-article", type=Path, required=True)
    parser.add_argument("--mda-article", type=Path, required=True)
    parser.add_argument("--blind-dir", type=Path, required=True)
    parser.add_argument("--private-key-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        for file in (args.manifest, args.control_article, args.mda_article):
            if file.stat().st_size > 128 * 1024:
                raise ValueError("arquivo excede 128 KiB")
        status = seal_pair(
            json.loads(args.manifest.read_text(encoding="utf-8")),
            args.control_article.read_text(encoding="utf-8"),
            args.mda_article.read_text(encoding="utf-8"),
            args.blind_dir, args.private_key_dir,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
