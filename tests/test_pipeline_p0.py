"""
Testes P0 — pipeline CLI (gates de validação/policy)
pytest tests/test_pipeline_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))


def _argv(link, *extra):
    return ["pipeline_p0.py", link, *extra]


def test_bloqueia_fail_exit2(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline_p0.DB_PATH", tmp_path / "p.db")
    with patch("pipeline_p0.validar_link_afiliado") as mv:
        mv.return_value = {"status_validacao": "FAIL", "plataforma": "Mercado Livre", "status": "sem tag"}
        import pipeline_p0, sys as _s
        _s.argv, old = _argv("https://www.mercadolivre.com.br/x"), _s.argv
        try:
            try:
                pipeline_p0.main()
                assert False
            except SystemExit as e:
                assert e.code == 2
        finally:
            _s.argv = old


def test_bloqueia_policy_fail_exit3(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline_p0.DB_PATH", tmp_path / "p.db")
    with patch("pipeline_p0.validar_link_afiliado") as mv, \
         patch("pipeline_p0.avaliar_politica") as mp:
        mv.return_value = {"status_validacao": "PASS", "plataforma": "Mercado Livre",
                           "possui_tag_rastreio": True, "status": "ok",
                           "url_final": "https://www.mercadolivre.com.br/p/MLB1?matt_word=x", "destino": "produto"}
        mp.return_value = {"status_politica": "FAIL", "programa": "mercado_livre",
                           "regras": [{"regra_id": "ML-COMPARISON", "evidencia": "comparação proibida"}]}
        import pipeline_p0, sys as _s
        _s.argv, old = _argv("https://www.mercadolivre.com.br/p/MLB1?matt_word=x"), _s.argv
        try:
            try:
                pipeline_p0.main()
                assert False
            except SystemExit as e:
                assert e.code == 3
        finally:
            _s.argv = old


def test_extrair_item_id():
    import pipeline_p0
    assert pipeline_p0.extrair_item_id("https://x/MLB123456789?matt_word=a") == "MLB123456789"
    assert pipeline_p0.extrair_item_id("https://x/sem-id") == ""
