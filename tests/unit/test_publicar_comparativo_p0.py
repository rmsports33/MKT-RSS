"""M04.17C — escrita de comparativo no WordPress via MCP.

Três blocos:
1. CONTRATO — o que vai para o servidor (endpoint, ferramenta, parâmetros);
2. REGRESSÃO — o caminho legado de NOTÍCIAS continua idêntico;
3. FALHAS — cada modo de erro devolve {"erro"} e NENHUMA requisição indevida.

Nada aqui fala com o WordPress: tudo é mockado. Nenhum post é criado.
"""
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0 import wp_publisher as W  # noqa: E402
from mkt_flow_p0.comparativo_contract import construir_contrato  # noqa: E402

AMAZON = "https://www.amazon.com.br/dp/B0XXX"
ML = "https://www.mercadolivre.com.br/pixel-11/p/MLB123"
SAMSUNG = "https://news.samsung.com/br/galaxy-s26"
GOOGLE = "https://store.google.com/pt/product/pixel_11"

MODELOS = [
    {"nome": "Galaxy S26", "specs": {"tela": "6,3 pol"}, "fonte": SAMSUNG},
    {"nome": "Pixel 11", "specs": {"tela": "6,4 pol"}, "fonte": GOOGLE},
]
HISTORICO = {
    "Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
    "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}],
}


def _contrato(**extra):
    dados = dict(
        modelos=MODELOS,
        price_history=HISTORICO,
        conteudo_html="<h1>Galaxy S26 vs Pixel 11</h1><p>Comparativo.</p>",
        titulo="Galaxy S26 vs Pixel 11 — Comparativo completo (celular)",
        categoria="celular",
        cat_slug="celular",
        veredito="O Galaxy S26 vence em bateria.",
        notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
        compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
        criterios=[{"label": "Bateria", "vals": ["5000 mAh", "4600 mAh"], "win": 0}],
    )
    dados.update(extra)
    return construir_contrato(**dados)


class _Resposta:
    def __init__(self, status_code=200, payload=None, texto=""):
        self.status_code = status_code
        self._payload = payload
        self.text = texto or ("" if payload is None else str(payload))

    def json(self):
        if self._payload is None:
            raise ValueError("nao-JSON")
        return self._payload


# --- 1. CONTRATO -------------------------------------------------------------

def test_publicar_comparativo_chama_o_mcp_com_create_comparativo():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {
            "post_id": 777, "status": "draft", "edit_link": "https://exemplo/wp-admin/post.php?post=777"}})
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert r["post_id"] == 777
    assert r["status"] == "draft"
    assert r["fonte"] == "mcp:create_comparativo"
    url = post.call_args[0][0]
    assert url == "https://exemplo.com.br/wp-json/conexo/v1/mcp/execute"
    corpo = post.call_args[1]["json"]
    assert corpo["tool"] == "create_comparativo"
    assert set(corpo["params"]) == {"title", "content", "products", "notas", "buys",
                                    "crits", "veredito", "cat_slug"}


def test_parametros_do_mcp_trazem_a_tabela_alinhada():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {"post_id": 1, "status": "draft"}})
        W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    params = post.call_args[1]["json"]["params"]
    assert params["products"] == ["Galaxy S26", "Pixel 11"]
    assert params["notas"] == [9.0, 8.5]
    assert params["buys"] == [AMAZON, ML]
    assert params["crits"][0]["label"] == "Bateria"
    assert params["crits"][0]["vals"] == ["5000 mAh", "4600 mAh"]


def test_content_vai_so_o_corpo():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {"post_id": 1, "status": "draft"}})
        W.publicar_comparativo(_contrato(conteudo_html=(
            "<!DOCTYPE html><html><head><title>x</title></head><body><p>corpo</p></body></html>")),
            "https://exemplo.com.br", "u", "p")
    conteudo = post.call_args[1]["json"]["params"]["content"]
    assert "<!DOCTYPE" not in conteudo
    assert "<html" not in conteudo.lower()
    assert "<head" not in conteudo.lower()
    assert "<p>corpo</p>" in conteudo


def test_authorization_vai_no_cabecalho():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {"post_id": 1, "status": "draft"}})
        W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "user", "senha")
    headers = post.call_args[1]["headers"]
    assert headers["Authorization"].startswith("Basic ")
    assert headers["Content-Type"] == "application/json"


# --- 2. REGRESSÃO do caminho legado de NOTÍCIAS -----------------------------

def test_assinatura_legada_de_publicar_no_wordpress_nao_mudou():
    """Estabilidade de contrato: a assinatura pública não pode mudar."""
    esperado = ["titulo", "conteudo_html", "status_validacao", "wp_url", "wp_user",
                "wp_app_password", "status_desejado", "categoria_ids", "tag_ids",
                "imagem_url", "timeout", "slug", "rank_math"]
    assert list(inspect.signature(W.publicar_no_wordpress).parameters) == esperado


def test_legado_ainda_cria_post_do_tipo_post():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(201, {"id": 42, "link": "https://exemplo/x", "status": "draft"})
        r = W.publicar_no_wordpress("Titulo", "<p>corpo</p>", "PASS",
                                    "https://exemplo.com.br", "u", "p")
    assert r["post_id"] == 42
    assert post.call_args[0][0] == "https://exemplo.com.br/wp-json/wp/v2/posts"
    corpo = post.call_args[1]["json"]
    assert corpo["status"] == "draft"
    assert "post_type" not in corpo  # tipo padrão do REST é post


def test_legado_ainda_bloqueia_publish_sem_pass():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = W.publicar_no_wordpress("Titulo", "<p>c</p>", "FAIL",
                                    "https://exemplo.com.br", "u", "p",
                                    status_desejado="publish")
    assert "erro" in r
    assert post.call_count == 0


def test_legado_mantem_forca_draft_quando_validacao_nao_e_pass():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(201, {"id": 43, "link": "l", "status": "draft"})
        W.publicar_no_wordpress("T", "<p>c</p>", "UNKNOWN",
                               "https://exemplo.com.br", "u", "p")
    assert post.call_args[1]["json"]["status"] == "draft"


def test_publicar_pagina_ainda_vai_para_pages():
    with patch("mkt_flow_p0.wp_publisher.requests.get") as busca, \
         patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        busca.return_value = _Resposta(200, [])
        post.return_value = _Resposta(201, {"id": 9, "link": "l"})
        W.publicar_pagina("Titulo", "<p>c</p>", "slug-x", "https://exemplo.com.br", "u", "p")
    assert post.call_args[0][0] == "https://exemplo.com.br/wp-json/wp/v2/pages"


# --- 3. FALHAS ---------------------------------------------------------------

def test_contrato_sem_evidencia_por_produto_nao_faz_requisicao():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
                 "Pixel 11": []}
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = W.publicar_comparativo(_contrato(price_history=historico),
                                   "https://exemplo.com.br", "u", "p")
    assert "erro" in r
    assert post.call_count == 0  # NENHUMA requisição ao WordPress


def test_content_com_documento_completo_e_recusado_sem_requisicao():
    contrato = _contrato()
    contrato["conteudo_html"] = "<!DOCTYPE html><html><body><p>x</p></body></html>"
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = W.publicar_comparativo(contrato, "https://exemplo.com.br", "u", "p")
    assert "erro" in r
    assert "documento" in r["erro"]
    assert post.call_count == 0


def test_credencial_ausente_nao_faz_requisicao():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        r = W.publicar_comparativo(_contrato(), "", "u", "p")
    assert "erro" in r
    assert post.call_count == 0


def test_mcp_que_recusa_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": False, "erro": "parametro invalido"})
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert r["erro"] == "parametro invalido"


def test_mcp_sem_post_id_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {"status": "draft"}})
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "post_id" in r["erro"]


def test_mcp_que_devolve_status_publicado_e_erro_fechado():
    """Se o MCP devolvesse 'publish', o publicador tem que recusar — e
    reportar o post_id para o post poder ser inspecionado."""
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, {"ok": True, "result": {"post_id": 55, "status": "publish"}})
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "erro" in r
    assert "draft" in r["erro"]
    assert r.get("post_id") == 55


def test_http_500_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(500, None, "erro interno")
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "erro" in r
    assert "500" in r["erro"]


def test_timeout_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.side_effect = requests.Timeout()
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "timeout" in r["erro"].lower()


def test_resposta_nao_json_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.return_value = _Resposta(200, None, "<html>nao json</html>")
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "erro" in r


def test_excecao_de_rede_devolve_erro():
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        post.side_effect = RuntimeError("rede caiu")
        r = W.publicar_comparativo(_contrato(), "https://exemplo.com.br", "u", "p")
    assert "erro" in r


def test_executar_ferramenta_mcp_exige_tool():
    r = W.executar_ferramenta_mcp("https://exemplo.com.br", "u", "p", "")
    assert "erro" in r
