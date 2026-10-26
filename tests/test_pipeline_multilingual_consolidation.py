"""Regression: multilingual references are passed into fail-closed RSS review."""
from pathlib import Path
from mkt_flow_p0.auditoria_cobertura_pos_ia import auditar_cobertura_pos_ia
from test_post_ai_claim_coverage import dados


def test_pipeline_passes_declared_translation_references():
    code = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    assert 'referencias_traducao=rw.get("referencias_traducao")' in code


def test_multilingual_reference_is_diagnostic_not_wp_authorization():
    contrato, capturas = dados()
    verdict = auditar_cobertura_pos_ia(
        "The product got an update.", contrato, capturas,
        referencias_traducao={"the product got an update.": ["c1"]})
    assert verdict["veredito"] == "REVISAO_SEMANTICA_PENDENTE"
    assert verdict["certificacao_factual"] is False
    assert verdict["autoriza_wordpress"] is False


def test_missing_or_invalid_reference_remains_blocked():
    contrato, capturas = dados()
    for mappings in (None, {"the product got an update.": ["unknown"]}):
        verdict = auditar_cobertura_pos_ia(
            "The product got an update.", contrato, capturas,
            referencias_traducao=mappings)
        assert verdict["veredito"] == "BLOQUEADO"


def test_pipeline_has_unconditional_no_wp_return():
    code = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    assert '"acao": "bloqueado"' in code
    assert '"escreveu": False' in code
    assert '"verificacao_factual": verificacao_factual' in code
