"""Prepare a no-cost controlled MDA A/B pilot. Never calls a provider or WordPress.

Usage (private local JSON; do NOT commit manuscript/prompt/output):
    python -m scripts.prepare_mda_ab --input /private/pilot.json --out /private/pilot_run

Input schema:
{
  "schema":"conexo-mda-ab-source/1", "case_id":"guia-9798",
  "title":"...", "source_name":"...", "source_text":"...",
  "editorial_brief":{"genre":"guia","reader":"...",...},
  "research_context":null,
  "intended_generation":{"model":"...", "temperature":0, "max_tokens":2200}
}
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from mkt_flow_p0.editorial_substance import brief_hash, normalize_brief
from mkt_flow_p0.rewriter import montar_prompt


def _digest(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_private(path, content):
    descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as fd:
        fd.write(content)


def build_pair(case):
    """Return control/MDA full prompts and a no-approval sanitized manifest."""
    required = {"schema", "case_id", "title", "source_name", "source_text",
                "editorial_brief", "research_context", "intended_generation"}
    if not isinstance(case, dict) or set(case) != required:
        raise ValueError("case schema inválido")
    if case["schema"] != "conexo-mda-ab-source/1":
        raise ValueError("case version inválida")
    identifier = case["case_id"]
    if (not isinstance(identifier, str) or not 3 <= len(identifier) <= 48
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in identifier)):
        raise ValueError("case_id inválido")
    for name in ("title", "source_name", "source_text"):
        if not isinstance(case[name], str) or not case[name].strip():
            raise ValueError("insumo vazio")
    if len(case["source_text"]) < 200 or len(case["source_text"]) > 60000:
        raise ValueError("insumo fora do limite")
    settings = case["intended_generation"]
    if (not isinstance(settings, dict)
            or set(settings) != {"model", "temperature", "max_tokens"}
            or not isinstance(settings["model"], str)
            or not 3 <= len(settings["model"]) <= 100
            or type(settings["temperature"]) not in (int, float)
            or not 0 <= settings["temperature"] <= 1
            or type(settings["max_tokens"]) is not int
            or not 500 <= settings["max_tokens"] <= 8000):
        raise ValueError("parâmetros de geração inválidos")
    brief = normalize_brief(case["editorial_brief"])
    context = case["research_context"]
    if context is not None and not isinstance(context, dict):
        raise ValueError("contexto inválido")

    common = dict(titulo_original=case["title"], texto_original=case["source_text"],
                  fonte_nome=case["source_name"], editorial_brief=brief,
                  contexto_complementar=context)
    control = montar_prompt(**common, voice_variant="control")
    mda = montar_prompt(**common, voice_variant="mda")
    if control == mda:
        raise ValueError("variações não distinguíveis")
    # The ONLY prompt difference must be the MDA guidance, not sources,
    # SEO rules, article facts, names, or author identity.
    from mkt_flow_p0.editorial_voice_adapter import writing_voice_guidance
    guidance = writing_voice_guidance(brief)
    if mda.count(guidance) != 1 or mda.replace(guidance, "") != control:
        raise ValueError("braços não comparáveis")
    manifest = {
        "schema": "conexo-mda-ab-preflight/1",
        "case_id": identifier, "genre": brief["genre"],
        "source_sha256": _digest(case["source_text"]),
        "brief_sha256": brief_hash(brief),
        "research_sha256": _digest(_canonical(context)),
        "control_prompt_sha256": _digest(control),
        "mda_prompt_sha256": _digest(mda),
        "intended_generation": settings,
        "only_delta": "mda_voice_guidance",
        "provider_called": False, "generated_articles_present": False,
        "external_blind_review_completed": False,
        "quality_improvement_demonstrated": False,
        "factual_approval": False, "publication_authorized": False,
        "wordpress_written": False,
    }
    return control, mda, manifest


def prepare_case(case, output_dir):
    """Write unpublished text ONLY inside a caller-designated private folder."""
    control, mda, manifest = build_pair(case)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    _write_private(output / "control.prompt.txt", control)
    _write_private(output / "mda.prompt.txt", mda)
    _write_private(output / "manifest.private.json",
                   json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest



def prepare_batch(batch, output_dir):
    """Batch preparation keeps all real manuscripts private and uses one source per pair."""
    if (not isinstance(batch, dict)
            or set(batch) != {"schema", "cases"}
            or batch["schema"] != "conexo-mda-ab-batch/1"
            or not isinstance(batch["cases"], list)
            or not 1 <= len(batch["cases"]) <= 8):
        raise ValueError("lote A/B inválido")
    # Validate the entire batch before creating any output directory.
    pairs = [build_pair(case) for case in batch["cases"]]
    names = [manifest["case_id"] for _, _, manifest in pairs]
    if len(set(names)) != len(names):
        raise ValueError("case_id duplicado")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    manifests = []
    for case in batch["cases"]:
        manifests.append(prepare_case(case, root / case["case_id"]))
    return {
        "schema": "conexo-mda-ab-batch-preflight/1",
        "count": len(manifests),
        "cases": manifests,
        "provider_called": False,
        "generated_articles_present": False,
        "independent_review_completed": False,
        "quality_improvement_demonstrated": False,
        "publication_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline MDA/control prompt preflight; no model requests")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    # A private file may contain an unpublished complete article.
    if args.input.stat().st_size > 128 * 1024:
        parser.error("arquivo de entrada excede limite")
    try:
        case = json.loads(args.input.read_text(encoding="utf-8"))
        manifest = (prepare_batch(case, args.out)
                    if isinstance(case, dict) and case.get("schema") == "conexo-mda-ab-batch/1"
                    else prepare_case(case, args.out))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    # Only hashes and state are emitted, never article, prompts or sources.
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
