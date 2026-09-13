"""
Expansão de suite 9: cobre branches não testados dos módulos novos.
pytest tests/unit/test_suite_expand.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mkt_flow_p0.content_filter import filtrar_por_tema, filtrar_conteudo, filtrar_item_rss
from mkt_flow_p0.format import markdown_para_html, truncar_palavras, sanitizar_url
import mkt_flow_p0.cloud_db as C

# --- tema ---
def test_tema_excluir_prioridade():
    assert filtrar_por_tema("Fase da lua cheia hoje", "")["veredito"] == "BLOQUEADO"
def test_tema_incluir_case():
    assert filtrar_por_tema("Review FONE JBL", "")["lista"] == "incluir"
def test_tema_vazio_sem_filtro():
    # sem texto = nenhum termo -> bloqueado por whitelist
    assert filtrar_por_tema("", "")["veredito"] == "BLOQUEADO"
def test_tema_whitelist_vazia_aprova(monkeypatch):
    import mkt_flow_p0.content_filter as F
    monkeypatch.setattr(F, "_TEMA", {"incluir": [], "excluir": []})
    assert F.filtrar_por_tema("qualquer", "")["veredito"] == "APROVADO"

# --- format ---
def test_md_bold_link_xss():
    h = markdown_para_html("**oi** [x](https://x) <script>")
    assert "<strong>oi</strong>" in h and "&lt;script&gt;" in h
def test_md_tabela_e_hr():
    # redator tem tabela; format principal não — valida hr
    h = markdown_para_html("Titulo\n\n---\n\nTexto")
    assert "<hr>" in h and "<p>Texto</p>" in h
def test_truncar_sem_corte():
    assert truncar_palavras("curto", 10) == "curto"
def test_truncar_corte_palavra():
    # 7 chars corta "um dois tres" em fronteira -> "um dois" ou "um" dependendo de limite
    assert truncar_palavras("um dois tres quatro", 7) in ("um", "um dois")
    assert truncar_palavras("Fabricantes opinam", 16) == "Fabricantes"
def test_sanitizar_controles():
    assert "\x00" not in sanitizar_url("https://x/\x00a\xad")
    assert sanitizar_url(" https://x.com/a ") == "https://x.com/a"

# --- cloud_db ---
def test_cloud_desligado(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert C.turso_enabled() is False
def test_cloud_encode_args():
    assert C._encode_arg(None)["type"] == "null"
    assert C._encode_arg(1)["type"] == "integer"
    assert C._encode_arg(1.5)["type"] == "float"
    assert C._encode_arg("a")["type"] == "text"
def test_cloud_execute_401(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "bad")
    m = MagicMock()
    m.status_code = 401
    m.text = "unauthorized"
    with patch("mkt_flow_p0.cloud_db.requests.post", return_value=m):
        assert "401" in C.turso_execute("SELECT 1")["erro"]
def test_cloud_timeout(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "https://db.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "tok")
    import requests
    with patch("mkt_flow_p0.cloud_db.requests.post", side_effect=requests.Timeout("t")):
        assert "timeout" in C.turso_execute("SELECT 1")["erro"].lower()

# --- content_filter bloqueio/revisao ---
def test_bloqueio_apostas():
    assert filtrar_conteudo("ganhe na bet365", "")["veredito"] == "BLOQUEADO"
def test_revisao_politica():
    # "senado" está em PADROES_REVISAO -> REVISAR
    assert filtrar_conteudo("senado vota marco", "")["veredito"] == "REVISAR"
def test_item_rss_gate():
    r = filtrar_item_rss({"titulo": "aposta esportiva", "resumo": "", "link": "u", "fonte": "f"})
    assert r["veredito"] == "BLOQUEADO"

# --- pipeline_rss branches ---
def test_pipeline_bloqueado_tema():
    import pipeline_rss as P
    with patch("mkt_flow_p0.content_filter.filtrar_por_tema", return_value={"veredito": "BLOQUEADO", "motivo": "off_topic", "termo": "lua"}):
        assert P.processar_item({"titulo": "lua", "resumo": "", "link": "u"})["acao"] == "bloqueado"
def test_pipeline_texto_curto():
    import pipeline_rss as P
    with patch("mkt_flow_p0.content_filter.filtrar_por_tema", return_value={"veredito": "APROVADO", "motivo": "tema_ok"}), \
         patch("mkt_flow_p0.content_filter.filtrar_item_rss", return_value={"veredito": "APROVADO", "categorias": []}), \
         patch("mkt_flow_p0.extractor.extrair_conteudo", return_value={"palavras": 10, "qualidade_ok": False}):
        assert P.processar_item({"titulo": "t", "link": "u"})["acao"] == "falha"
def test_pipeline_init_db_migracao(tmp_path, monkeypatch):
    import pipeline_rss as P, sqlite3
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "mig.db")
    P.init_db()
    # cria sem colunas novas, depois migra
    con = sqlite3.connect(tmp_path / "mig.db")
    con.execute("DROP TABLE rss_runs")
    con.execute("CREATE TABLE rss_runs (id TEXT PRIMARY KEY, fonte TEXT)")
    con.commit()
    con.close()
    P.init_db()
    con = sqlite3.connect(tmp_path / "mig.db")
    cols = [r[1] for r in con.execute("PRAGMA table_info(rss_runs)").fetchall()]
    assert "custo_usd" in cols and "tokens_total" in cols
