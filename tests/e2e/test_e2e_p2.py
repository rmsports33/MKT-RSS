"""
Testes P2.2 — E2E pipeline completo com mocks
pytest tests/test_e2e_p2.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(autouse=True)
def _sem_turso_no_ambiente(monkeypatch):
    """E2E chama main(), que carrega .env (efeito global); não vazar TURSO_* para a sessão."""
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

def test_e2e_pipeline_completo(tmp_path, monkeypatch):
    # Isola DB
    db_path = tmp_path / "e2e.db"
    monkeypatch.setattr("pipeline_p0.DB_PATH", db_path)
    import mkt_flow_p0.link_tracker as lt
    import mkt_flow_p0.scheduler as sched
    monkeypatch.setattr(lt, "DB_PATH", db_path)
    monkeypatch.setattr(sched, "DB_PATH", db_path)
    # Mock WP env
    monkeypatch.setenv("WP_URL", "https://exemplo.com")
    monkeypatch.setenv("WP_USER", "user")
    monkeypatch.setenv("WP_APP_PASSWORD", "xxxx xxxx xxxx")
    # Mock validator PASS, api_ml sucesso, wp sucesso
    with patch("pipeline_p0.validar_link_afiliado") as mock_val, \
         patch("pipeline_p0.consultar_api_publica_mercado_livre") as mock_api, \
         patch("mkt_flow_p0.wp_publisher.publicar_no_wordpress") as mock_wp:
        mock_val.return_value = {
            "status_validacao": "PASS", "valido": True, "plataforma": "Mercado Livre",
            "possui_tag_rastreio": True, "status": "ok", "url_final": "https://www.mercadolivre.com.br/p/MLB123456789?matt_word=x"
        }
        mock_api.return_value = {
            "titulo": "Produto E2E Teste", "preco": 199.90, "estoque": 10, "status": "active",
            "imagens": ["https://example.com/img.jpg"], "categoria_id": "MLB123"
        }
        mock_wp.return_value = {"post_id": 999, "link": "https://exemplo.com/p/999", "status": "draft", "status_validacao": "PASS"}

        # Executa pipeline via função main com args mockados
        import pipeline_p0
        import sys as _sys
        orig_argv = _sys.argv
        _sys.argv = ["pipeline_p0.py", "https://www.mercadolivre.com.br/p/MLB123456789?matt_word=x"]
        # Muda cwd para tmp_path para não poluir raiz
        orig_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            pipeline_p0.main()
        except SystemExit as e:
            assert e.code == 0 or e.code is None
        finally:
            _sys.argv = orig_argv
            os.chdir(orig_cwd)

        # Verificações
        import sqlite3
        con = sqlite3.connect(db_path)
        cur = con.execute("SELECT COUNT(*) FROM pipeline_runs")
        assert cur.fetchone()[0] == 1
        cur = con.execute("SELECT COUNT(*) FROM link_publicacoes WHERE plataforma='wordpress'")
        assert cur.fetchone()[0] == 1
        cur = con.execute("SELECT COUNT(*) FROM link_publicacoes WHERE plataforma='site_estatico'")
        assert cur.fetchone()[0] == 1
        con.close()
        # Landing foi criada em tmp_path
        landings = list(tmp_path.glob("landing_*.html"))
        assert len(landings) == 1
        html = landings[0].read_text(encoding="utf-8")
        assert "#ad #linkdeafiliado" in html
        assert "Produto E2E Teste" in html
        # SEO check
        from mkt_flow_p0.seo import validar_seo_qualidade
        chk = validar_seo_qualidade(html)
        assert chk["tem_title"]
        assert chk["tem_canonical"]
        # Sitemap foi gerado com URL http
        sitemap = tmp_path / "sitemap.xml"
        assert sitemap.exists()
        assert "exemplo.com/p/999" in sitemap.read_text(encoding="utf-8")

def test_e2e_bloqueia_fail_nao_gera(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline_p0.DB_PATH", tmp_path / "e2e2.db")
    import mkt_flow_p0.link_tracker as lt
    monkeypatch.setattr(lt, "DB_PATH", tmp_path / "e2e2.db")
    with patch("pipeline_p0.validar_link_afiliado") as mock_val:
        mock_val.return_value = {
            "status_validacao": "FAIL", "valido": False, "plataforma": "Mercado Livre",
            "possui_tag_rastreio": False, "status": "sem tag", "url_final": "https://www.mercadolivre.com.br/p/MLB1"
        }
        import pipeline_p0, sys as _sys, os
        orig_argv = _sys.argv
        _sys.argv = ["pipeline_p0.py", "https://www.mercadolivre.com.br/p/MLB1"]
        orig_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            try:
                pipeline_p0.main()
                assert False, "deveria ter exit 2"
            except SystemExit as e:
                assert e.code == 2
        finally:
            _sys.argv = orig_argv
            os.chdir(orig_cwd)
        # Não deve ter gerado landing
        assert len(list(tmp_path.glob("landing_*.html"))) == 0

if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_"):
            fn()
            print(f"[OK] {n}")
