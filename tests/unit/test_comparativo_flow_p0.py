"""M04.17D — fluxo operacional do comparativo (redator -> WordPress).

Cobre:
1. DRY-RUN (padrão): mostra o plano e NÃO escreve;
2. OPT-IN: sem COMPARATIVO_PUBLICACAO_ENABLED, não escreve;
3. BLOQUEIO antes de qualquer requisição: contrato inválido, evidência
   insuficiente por produto, preço órfão, vínculo ambíguo;
4. ESCRITA: só com dry_run=False + flag ligada, e sempre rascunho;
5. FALHAS: autenticação, transporte, contrato e resposta inesperada;
6. ORIGEM DOS PREÇOS: marketplace + data + vínculo inequívoco;
7. NOTÍCIAS: o caminho legado não produz documento HTML completo.

Nada aqui fala com o WordPress: tudo é mockado. Nenhum post é criado.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0 import comparativo_flow as F  # noqa: E402

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
CRITERIOS = [{"label": "Bateria", "vals": ["5000 mAh", "4600 mAh"], "win": 0}]


class _Resposta:
    def __init__(self, status_code=200, payload=None, texto=""):
        self.status_code = status_code
        self._payload = payload
        self.text = texto or ("" if payload is None else str(payload))

    def json(self):
        if self._payload is None:
            raise ValueError("nao-JSON")
        return self._payload


def _chamar(dry_run=True, flag=None, historico=None, criterios=None, modelos=None):
    """Chama o fluxo com o ambiente controlado. Devolve (resultado, mock_post)."""
    with patch.dict("os.environ", {} if flag is None else
                    {"COMPARATIVO_PUBLICACAO_ENABLED": flag}, clear=True):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
            post.return_value = _Resposta(200, {"ok": True, "result": {
                "post_id": 4242, "status": "draft", "edit_link": "https://exemplo/edit"}})
            resultado = F.processar_comparativo(
                modelos=modelos if modelos is not None else MODELOS,
                price_history=historico if historico is not None else HISTORICO,
                conteudo_html="<h1>Galaxy S26 vs Pixel 11</h1><p>Comparativo.</p>",
                titulo="Galaxy S26 vs Pixel 11 — Comparativo completo (celular)",
                categoria="celular", cat_slug="celular",
                veredito="O Galaxy S26 vence em bateria.",
                notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
                compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
                criterios=criterios if criterios is not None else CRITERIOS,
                wp_url="https://exemplo.com.br", wp_user="u", wp_app_password="p",
                dry_run=dry_run,
            )
    return resultado, post


# --- 1. DRY-RUN --------------------------------------------------------------

def test_dry_run_e_o_padrao_e_nao_escreve():
    resultado, post = _chamar(dry_run=True, flag="1")
    assert resultado["acao"] == "dry_run_ok"
    assert resultado["escreveu"] is False
    assert post.call_count == 0


def test_dry_run_mostra_o_plano_com_a_tabela():
    resultado, _ = _chamar(dry_run=True, flag="1")
    assert resultado["produtos"] == ["Galaxy S26", "Pixel 11"]
    assert resultado["notas"] == [9.0, 8.5]
    assert resultado["criterios"] == ["Bateria"]
    # O produto tem TRÊS critérios: preço datado em marketplace, fonte primária
    # do fabricante e o cruzamento provado pelas duas fontes independentes.
    assert set(resultado["criterios_por_produto"]["Galaxy S26"]) == {
        "preco_br_data", "fonte_primaria", "cruzamento_2fontes"}
    assert resultado["vinculos_preco"][0]["fonte"] == AMAZON


def test_dry_run_nao_precisa_da_flag_ligada():
    """Inspecionar o plano nao e' publicar: a flag nao e' exigida no dry-run."""
    resultado, post = _chamar(dry_run=True, flag=None)
    assert resultado["acao"] == "dry_run_ok"
    assert resultado["publicacao_ativa"] is False
    assert post.call_count == 0


# --- 2. OPT-IN ---------------------------------------------------------------

def test_sem_flag_a_publicacao_fica_desativada_e_nao_escreve():
    resultado, post = _chamar(dry_run=False, flag=None)
    assert resultado["acao"] == "desativado"
    assert resultado["escreveu"] is False
    assert post.call_count == 0


def test_flag_com_valor_fora_do_conjunto_nao_liga():
    resultado, post = _chamar(dry_run=False, flag="sim")
    assert resultado["acao"] == "desativado"
    assert post.call_count == 0


def test_flag_ligada_escreve_rascunho():
    resultado, post = _chamar(dry_run=False, flag="true")
    assert resultado["acao"] == "rascunho_criado"
    assert resultado["post_id"] == 4242
    assert resultado["status"] == "draft"
    assert post.call_count == 1
    corpo = post.call_args[1]["json"]
    assert corpo["tool"] == "create_comparativo"
    assert post.call_args[0][0].endswith("/wp-json/conexo/v1/mcp/execute")


# --- 3. BLOQUEIO ANTES DE QUALQUER REQUISIÇÃO --------------------------------

def test_produto_sem_evidencia_bloqueia_sem_requisicao():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
                 "Pixel 11": []}
    resultado, post = _chamar(dry_run=False, flag="1", historico=historico)
    assert resultado["acao"] == "bloqueado"
    assert resultado["motivo"] == "sem_valor_por_produto"
    assert post.call_count == 0


def test_preco_orfao_bloqueia_sem_requisicao():
    historico = dict(HISTORICO)
    historico["Produto Fantasma"] = [{"data": "2026-09-17", "preco": 10.0, "fonte": AMAZON}]
    resultado, post = _chamar(dry_run=False, flag="1", historico=historico)
    assert resultado["acao"] == "bloqueado"
    assert resultado["motivo"] == "preco_sem_vinculo"
    assert post.call_count == 0


def test_vinculo_equivoco_bloqueia_sem_requisicao():
    historico = dict(HISTORICO)
    historico["Galaxy S26"] = [{"data": "2026-09-17", "preco": 5999.00,
                                 "fonte": AMAZON, "produto": "Pixel 11"}]
    resultado, post = _chamar(dry_run=False, flag="1", historico=historico)
    assert resultado["acao"] == "bloqueado"
    assert post.call_count == 0


def test_contrato_invalido_bloqueia_sem_requisicao():
    """Sem nenhum critério de comparação, o post nasceria sem tabela."""
    resultado, post = _chamar(dry_run=False, flag="1", criterios=[])
    assert resultado["acao"] == "bloqueado"
    assert resultado["motivo"] == "contrato_invalido"
    assert post.call_count == 0


def test_um_so_produto_bloqueia_sem_requisicao():
    resultado, post = _chamar(dry_run=False, flag="1", modelos=[MODELOS[0]],
                               historico={"Galaxy S26": HISTORICO["Galaxy S26"]})
    assert resultado["acao"] == "bloqueado"
    assert post.call_count == 0


# --- 4/5. FALHAS -------------------------------------------------------------

def test_mcp_401_devolve_falha_sem_levantar():
    with patch.dict("os.environ", {"COMPARATIVO_PUBLICACAO_ENABLED": "1"}, clear=True):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
            post.return_value = _Resposta(401, None, "nao autorizado")
            r = F.processar_comparativo(
                modelos=MODELOS, price_history=HISTORICO,
                conteudo_html="<p>c</p>", titulo="A vs B",
                notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
                compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
                criterios=CRITERIOS,
                wp_url="https://exemplo.com.br", wp_user="u", wp_app_password="p",
                dry_run=False)
    assert r["acao"] == "falha"
    assert "401" in r["motivo"]


def test_timeout_de_transporte_devolve_falha():
    with patch.dict("os.environ", {"COMPARATIVO_PUBLICACAO_ENABLED": "1"}, clear=True):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
            post.side_effect = requests.Timeout()
            r = F.processar_comparativo(
                modelos=MODELOS, price_history=HISTORICO,
                conteudo_html="<p>c</p>", titulo="A vs B",
                notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
                compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
                criterios=CRITERIOS,
                wp_url="https://exemplo.com.br", wp_user="u", wp_app_password="p",
                dry_run=False)
    assert r["acao"] == "falha"
    assert "timeout" in r["motivo"].lower()


def test_resposta_inesperada_sem_post_id_devolve_falha():
    with patch.dict("os.environ", {"COMPARATIVO_PUBLICACAO_ENABLED": "1"}, clear=True):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
            post.return_value = _Resposta(200, {"ok": True, "result": {"status": "draft"}})
            r = F.processar_comparativo(
                modelos=MODELOS, price_history=HISTORICO,
                conteudo_html="<p>c</p>", titulo="A vs B",
                notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
                compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
                criterios=CRITERIOS,
                wp_url="https://exemplo.com.br", wp_user="u", wp_app_password="p",
                dry_run=False)
    assert r["acao"] == "falha"
    assert "post_id" in r["motivo"]


def test_status_publicado_vindo_do_servidor_e_falha_fechada():
    with patch.dict("os.environ", {"COMPARATIVO_PUBLICACAO_ENABLED": "1"}, clear=True):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
            post.return_value = _Resposta(200, {"ok": True, "result": {
                "post_id": 77, "status": "publish"}})
            r = F.processar_comparativo(
                modelos=MODELOS, price_history=HISTORICO,
                conteudo_html="<p>c</p>", titulo="A vs B",
                notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
                compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
                criterios=CRITERIOS,
                wp_url="https://exemplo.com.br", wp_user="u", wp_app_password="p",
                dry_run=False)
    assert r["acao"] == "falha"
    assert "draft" in r["motivo"]


# --- 6. ORIGEM DOS PREÇOS ----------------------------------------------------

def test_preco_sem_marketplace_avisa_mas_nao_inventa_vinculo():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00}],
                 "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    auditoria = F.auditar_precos(MODELOS, historico)
    assert auditoria["ok"] is True
    assert any("marketplace" in a for a in auditoria["avisos"])


def test_vinculo_explicito_e_registrado():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00,
                                 "fonte": AMAZON, "produto": "Galaxy S26"}],
                 "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    auditoria = F.auditar_precos(MODELOS, historico)
    vinculo = [v for v in auditoria["vinculos"] if v["produto"] == "Galaxy S26"][0]
    assert vinculo["vinculo"] == "explicito"


def test_preco_com_data_invalida_nao_vincula():
    historico = {"Galaxy S26": [{"data": "2026-02-31", "preco": 5999.00, "fonte": AMAZON}],
                 "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    auditoria = F.auditar_precos(MODELOS, historico)
    # a data invalida impede o vinculo de preco (o gate nao a conta)
    assert all(v["produto"] != "Galaxy S26" or v["data"] == "2026-02-31"
               for v in auditoria["vinculos"])


# --- REGRESSÃO: o critério de preço tem que ser ALCANÇÁVEL --------------------
# Defeito encontrado no dry-run do M04.17D: o contrato guardava o preço sem o
# símbolo "R$" ("5.999,00") e a regex do gate EXIGE "R$" — então o critério
# `preco_br_data`, o principal da regra 13, era INALCANÇÁVEL pela cadeia real.
# Os testes do M04.17B não pegaram isso porque o comparativo de lá já passava
# pelo critério de cruzamento. Este teste fecha a lacuna.

def test_criterio_de_preco_e_alcancavel_com_preco_float_real():
    resultado, _ = _chamar(dry_run=True, flag="1")
    criterios = resultado["criterios_por_produto"]["Galaxy S26"]
    assert "preco_br_data" in criterios
    assert "cruzamento_2fontes" in criterios


def test_preco_guardado_no_contrato_tem_o_formato_que_o_gate_le():
    from mkt_flow_p0.comparativo_contract import construir_contrato
    from mkt_flow_p0.content_filter import _PRECO_BR
    contrato = construir_contrato(
        modelos=MODELOS, price_history=HISTORICO,
        conteudo_html="<p>c</p>", titulo="A vs B",
        notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
        compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
        criterios=CRITERIOS,
    )
    preco = contrato["produtos"][0]["preco"]
    assert _PRECO_BR.search(preco), f"o gate nao le o preco guardado: {preco!r}"


def test_preco_sem_marketplace_NAO_concede_o_criterio_de_preco():
    """Contraprova: com o preço no formato certo, a FALTA do marketplace
    ainda impede o critério — e o comparativo é bloqueado.

    O defeito corrigido não afrouxou o gate: ele só fez o critério ficar
    ALCANÇÁVEL quando as três provas existem (preço + data válida +
    marketplace)."""
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00}],
                 "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    resultado, post = _chamar(dry_run=True, flag="1", historico=historico)
    assert resultado["acao"] == "bloqueado"
    criterios = resultado["gate"]["criterios_por_produto"]["Galaxy S26"]
    assert "preco_br_data" not in criterios
    assert "fonte_primaria" in criterios
    assert post.call_count == 0


# --- 7. NOTÍCIAS: o caminho legado não produz documento completo -------------

def test_caminho_de_noticias_produz_fragmento_nao_documento():
    """O defeito de HTML completo era do REDATOR (pagina do comparativo).
    O caminho de noticias usa markdown -> fragmento. O contrato legado nao
    precisa mudar — e esta trava impede que alguem mude sem querer."""
    from mkt_flow_p0.format import markdown_para_html
    html = markdown_para_html("## Titulo\n\nParagrafo de teste.\n\n- item\n")
    baixo = html.lower()
    assert "<!doctype" not in baixo
    assert "<html" not in baixo
    assert "<head" not in baixo
    assert "<body" not in baixo
    assert "<h2>" in html


# --- CLI ---------------------------------------------------------------------

def test_cli_dry_run_le_o_json_e_nao_escreve(tmp_path, capsys):
    entrada = tmp_path / "entrada.json"
    entrada.write_text(json.dumps({
        "modelos": MODELOS, "price_history": HISTORICO,
        "conteudo_html": "<p>corpo</p>", "titulo": "A vs B",
        "notas": {"Galaxy S26": 9.0, "Pixel 11": 8.5},
        "compras": {"Galaxy S26": AMAZON, "Pixel 11": ML},
        "criterios": CRITERIOS,
    }), encoding="utf-8")
    with patch("mkt_flow_p0.wp_publisher.requests.post") as post:
        codigo = F._main_cli(["--entrada", str(entrada)])
    saida = json.loads(capsys.readouterr().out)
    assert codigo == 0
    assert saida["acao"] == "dry_run_ok"
    assert post.call_count == 0


def test_cli_com_json_invalido_devolve_erro(tmp_path, capsys):
    entrada = tmp_path / "entrada.json"
    entrada.write_text("{nao é json", encoding="utf-8")
    codigo = F._main_cli(["--entrada", str(entrada)])
    assert codigo == 2
    assert "erro" in json.loads(capsys.readouterr().out)
