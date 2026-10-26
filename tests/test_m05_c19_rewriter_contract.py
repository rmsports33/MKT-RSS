"""The LLM response cannot self-certify factual evidence."""
from pathlib import Path


def test_legacy_rewriter_returns_no_approved_contract():
    src = (Path(__file__).resolve().parents[1] / "mkt_flow_p0" / "rewriter.py").read_text(encoding="utf-8")
    assert "contrato_editorial = None" in src
    assert '"contrato_editorial": contrato_editorial' in src


def test_missing_rewriter_contract_fails_closed():
    from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias

    assert avaliar_evidencias(None)["veredito"] == "BLOQUEADO"
