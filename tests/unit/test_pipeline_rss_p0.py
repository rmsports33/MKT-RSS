"""
Testes P0 — pipeline_rss (tudo mockado, sem rede/LLM/WP)
pytest tests/test_pipeline_rss_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline_rss

ITEM = {"titulo": "Novo notebook", "resumo": "Review", "link": "https://x/n", "fonte": "blog"}


def _fluxo_ok(**kw):
    return {"acao": "publicado_rascunho", "run_id": "abc", "titulo_seo": "T", "palavras": 500, "wp": {}}


def test_bloqueado_na_pauta():
    with patch("mkt_flow_p0.content_filter.filtrar_item_rss",
               return_value={"veredito": "BLOQUEADO", "categorias": ["apostas"]}):
        import pipeline_rss as P
        r = P.processar_item(ITEM)
        assert r["acao"] == "bloqueado"


def test_falha_texto_curto():
    with patch("mkt_flow_p0.content_filter.filtrar_item_rss",
               return_value={"veredito": "APROVADO", "categorias": []}), \
         patch("mkt_flow_p0.extractor.extrair_conteudo",
               return_value={"palavras": 30, "qualidade_ok": False, "texto": "curto"}):
        import pipeline_rss as P
        assert P.processar_item(ITEM)["acao"] == "falha"


def test_dry_run_ok():
    ext = {"titulo": "T", "texto": "corpo " * 500, "palavras": 500, "qualidade_ok": True, "imagem": ""}
    with patch("mkt_flow_p0.content_filter.filtrar_item_rss",
               return_value={"veredito": "APROVADO", "categorias": []}), \
         patch("mkt_flow_p0.extractor.extrair_conteudo", return_value=ext), \
         patch("mkt_flow_p0.content_filter.filtrar_conteudo",
               return_value={"veredito": "APROVADO", "categorias": [], "trechos": [], "total_sinais": 0}):
        import pipeline_rss as P
        r = P.processar_item(ITEM, dry_run=True)
        assert r["acao"] == "dry_run_ok" and r["palavras"] == 500


def test_publicado_rascunho_mockado(tmp_path, monkeypatch):
    import pipeline_rss as P
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "rss.db")
    ext = {"titulo": "T", "texto": "corpo " * 500, "palavras": 500, "qualidade_ok": True, "imagem": ""}
    rw = {"titulo_seo": "Titulo SEO", "meta_description": "m", "slug": "s", "tags": ["t"],
          "texto_markdown": "texto " * 300, "palavras": 300}
    with patch("mkt_flow_p0.content_filter.filtrar_item_rss",
               return_value={"veredito": "APROVADO", "categorias": []}), \
         patch("mkt_flow_p0.extractor.extrair_conteudo", return_value=ext), \
         patch("mkt_flow_p0.content_filter.filtrar_conteudo",
               return_value={"veredito": "APROVADO", "categorias": [], "trechos": [], "total_sinais": 0}), \
         patch("mkt_flow_p0.rewriter.reescrever_materia", return_value=rw), \
         patch.dict("os.environ", {}, clear=False):
        monkeypatch.delenv("WP_URL", raising=False)
        r = P.processar_item(ITEM)
        assert r["acao"] == "publicado_rascunho" and r["run_id"]
