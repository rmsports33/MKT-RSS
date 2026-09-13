"""
Testes — custo real (8): rpc mede usage e grava no DB
pytest tests/unit/test_custo_real.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import pipeline_rss as P


def test_custo_gravado(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "c.db")
    ext = {"titulo": "T", "texto": "corpo " * 500, "palavras": 500, "qualidade_ok": True, "imagem": ""}
    rw = {"titulo_seo": "T", "meta_description": "m", "slug": "s", "tags": [], "texto_markdown": "x " * 300,
          "palavras": 300, "uso_tokens": {"total": 1234}, "custo_usd_estimado": 0.0015}
    with patch("mkt_flow_p0.content_filter.filtrar_por_tema", return_value={"veredito": "APROVADO"}), \
         patch("mkt_flow_p0.content_filter.filtrar_item_rss", return_value={"veredito": "APROVADO", "categorias": []}), \
         patch("mkt_flow_p0.extractor.extrair_conteudo", return_value=ext), \
         patch("mkt_flow_p0.content_filter.filtrar_conteudo", return_value={"veredito": "APROVADO", "categorias": [], "trechos": [], "total_sinais": 0}), \
         patch("mkt_flow_p0.rewriter.reescrever_materia", return_value=rw), \
         patch.dict("os.environ", {}, clear=False):
        monkeypatch.delenv("WP_URL", raising=False)
        r = P.processar_item({"titulo": "T", "resumo": "t", "link": "https://x", "fonte": "blog"})
        assert r["custo_usd"] == 0.0015 and r["tokens"] == 1234
    import sqlite3
    con = sqlite3.connect(tmp_path / "c.db")
    row = con.execute("SELECT custo_usd, tokens_total FROM rss_runs").fetchone()
    assert row[0] == 0.0015 and row[1] == 1234
