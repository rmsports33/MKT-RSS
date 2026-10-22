"""M04.17B — adaptador `gerar_comparativo` → `create_comparativo`.

Cobre o contrato estruturado, a validação fail-closed, a ponte com o gate de
valor POR PRODUTO (M04.17A) e a conversão para os parâmetros exatos do MCP.

Rodar:  python -m pytest tests/unit/test_comparativo_contract_p0.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0.comparativo_contract import (  # noqa: E402
    ContratoInvalido,
    avaliar_contrato,
    construir_contrato,
    contrato_para_mcp,
    extrair_corpo_html,
    normalizar_data_captura,
    normalizar_preco,
    validar_contrato,
)

AMAZON = "https://www.amazon.com.br/dp/B0XXX"
ML = "https://www.mercadolivre.com.br/pixel-11/p/MLB123"
SAMSUNG = "https://news.samsung.com/br/galaxy-s26"
GOOGLE = "https://store.google.com/pt/product/pixel_11"

PAGINA_COMPLETA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Galaxy S26 vs Pixel 11</title>
  <script type="application/ld+json">{"@type":"Article"}</script>
</head>
<body>
  <h1>Galaxy S26 vs Pixel 11</h1>
  <p>Comparativo com ficha técnica.</p>
  <script src="https://cdn.jsdelivr.net/chart.js"></script>
</body>
</html>
"""

MODELOS = [
    {"nome": "Galaxy S26", "specs": {"tela": "6,3 pol"}, "fonte": SAMSUNG},
    {"nome": "Pixel 11", "specs": {"tela": "6,4 pol"}, "fonte": GOOGLE},
]

HISTORICO_COM_FONTE = {
    "Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
    "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}],
}


def _contrato_completo(**extra):
    dados = dict(
        modelos=MODELOS,
        price_history=HISTORICO_COM_FONTE,
        conteudo_html=PAGINA_COMPLETA,
        titulo="Galaxy S26 vs Pixel 11 — Comparativo completo (celular)",
        categoria="celular",
        cat_slug="celular",
        veredito="O Galaxy S26 vence em bateria; o Pixel 11 em拍照? nao: em camera.",
        notas={"Galaxy S26": 9.0, "Pixel 11": 8.5},
        compras={"Galaxy S26": AMAZON, "Pixel 11": ML},
        criterios=[
            {"label": "Bateria", "vals": ["5000 mAh", "4600 mAh"], "win": 0},
            {"label": "Preço", "vals": ["R$ 5.999,00", "R$ 4.299,00"], "win": 1},
        ],
    )
    dados.update(extra)
    return construir_contrato(**dados)


# --- Normalizadores ----------------------------------------------------------

def test_data_iso_vira_brasileira():
    assert normalizar_data_captura("2026-09-17") == "17/09/2026"


def test_data_brasileira_e_mantida():
    assert normalizar_data_captura("17/09/2026") == "17/09/2026"


def test_data_que_nao_existe_e_rejeitada():
    assert normalizar_data_captura("2026-02-31") == ""
    assert normalizar_data_captura("31/02/2026") == ""


def test_preco_float_vira_ptbr():
    assert normalizar_preco(5999.00) == "5.999,00"


def test_preco_string_ptbr_e_mantido():
    assert normalizar_preco("1.600,00") == "1.600,00"


def test_preco_none_e_vazio():
    assert normalizar_preco(None) == ""
    assert normalizar_preco("") == ""
    assert normalizar_preco("R$ None") == ""


# --- HTML --------------------------------------------------------------------

def test_pagina_completa_vira_so_corpo():
    corpo = extrair_corpo_html(PAGINA_COMPLETA)
    assert "<h1>" in corpo and "Comparativo com ficha" in corpo
    assert "<!DOCTYPE" not in corpo
    assert "<html" not in corpo.lower()
    assert "<head" not in corpo.lower()
    assert "<script" not in corpo.lower()


def test_fragmento_sem_body_passa_direto():
    assert extrair_corpo_html("<p>so um paragrafo</p>") == "<p>so um paragrafo</p>"


# --- Construção do contrato -------------------------------------------------

def test_contrato_carrega_preco_e_data_de_cada_produto():
    contrato = _contrato_completo()
    galaxy = contrato["produtos"][0]
    pixel = contrato["produtos"][1]
    assert galaxy["preco"] == "R$ 5.999,00"
    assert galaxy["data_captura"] == "17/09/2026"
    assert galaxy["fonte_preco"] == AMAZON
    assert pixel["preco"] == "R$ 4.299,00"
    assert pixel["data_captura"] == "17/09/2026"
    assert pixel["fonte_preco"] == ML


def test_contrato_preserva_evidence_individual():
    """A evidência é POR PRODUTO — é o que o M04.17A exige."""
    contrato = _contrato_completo()
    assert contrato["produtos"][0]["fonte"] == SAMSUNG
    assert contrato["produtos"][1]["fonte"] == GOOGLE
    assert contrato["produtos"][0]["ficha"] == {"tela": "6,3 pol"}


def test_preco_sem_fonte_de_marketplace_fica_sem_evidencia():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00}],
                 "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    contrato = _contrato_completo(price_history=historico)
    assert contrato["produtos"][0]["preco"] == "R$ 5.999,00"
    assert contrato["produtos"][0]["fonte_preco"] == ""
    # o preço existe, mas SEM link de marketplace o gate nao aprova por preco
    avaliacao = avaliar_contrato(contrato)
    assert avaliacao["gate"]["criterios_por_produto"]["Galaxy S26"] == ["fonte_primaria"]
    assert "preco_br_data" not in avaliacao["gate"]["criterios_por_produto"]["Galaxy S26"]


def test_ultimo_ponto_valido_vence():
    historico = {"Galaxy S26": [
        {"data": "2026-09-01", "preco": 6999.00, "fonte": AMAZON},
        {"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON},
        {"data": "2026-09-18", "preco": None, "fonte": AMAZON},
    ], "Pixel 11": [{"data": "2026-09-17", "preco": 4299.00, "fonte": ML}]}
    contrato = _contrato_completo(price_history=historico)
    assert contrato["produtos"][0]["preco"] == "R$ 5.999,00"
    assert contrato["produtos"][0]["data_captura"] == "17/09/2026"


# --- Validação fail-closed ---------------------------------------------------

def test_contrato_incompleto_reprova():
    contrato = _contrato_completo(titulo="")
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("titulo" in e for e in validacao["erros"])


def test_contrato_de_um_produto_reprova():
    contrato = _contrato_completo(modelos=[MODELOS[0]], price_history={"Galaxy S26": []})
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("2 ou 3 produtos" in e for e in validacao["erros"])


def test_quatro_produtos_reprova_porque_o_mcp_trunca():
    """O MCP trunca em 3 e perderia a evidencia do 4o EM SILENCIO."""
    modelos = MODELOS + [
        {"nome": "Extra 1", "specs": {}, "fonte": SAMSUNG},
        {"nome": "Extra 2", "specs": {}, "fonte": SAMSUNG},
    ]
    historico = dict(HISTORICO_COM_FONTE)
    historico["Extra 1"] = [{"data": "2026-09-17", "preco": 100.0, "fonte": AMAZON}]
    historico["Extra 2"] = [{"data": "2026-09-17", "preco": 200.0, "fonte": AMAZON}]
    contrato = _contrato_completo(modelos=modelos, price_history=historico)
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("trunca em 3" in e for e in validacao["erros"])


def test_produto_sem_nota_reprova():
    contrato = _contrato_completo(notas={"Galaxy S26": 9.0})
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("sem nota" in e for e in validacao["erros"])


def test_nota_fora_de_faixa_reprova():
    contrato = _contrato_completo(notas={"Galaxy S26": 12, "Pixel 11": 8.5})
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("fora de 0-10" in e for e in validacao["erros"])


def test_link_de_compra_invalido_reprova():
    contrato = _contrato_completo(compras={"Galaxy S26": "javascript:alert(1)",
                                            "Pixel 11": ML})
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("link de compra invalido" in e for e in validacao["erros"])


def test_criterio_desalinhado_reprova():
    contrato = _contrato_completo(criterios=[{"label": "Bateria", "vals": ["5000 mAh"], "win": 0}])
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("desalinhada" in e for e in validacao["erros"])


def test_criterio_repetido_reprova():
    contrato = _contrato_completo(criterios=[
        {"label": "Bateria", "vals": ["a", "b"], "win": 0},
        {"label": "Bateria", "vals": ["c", "d"], "win": 1},
    ])
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("repetido" in e for e in validacao["erros"])


def test_vencedor_fora_de_faixa_reprova():
    contrato = _contrato_completo(criterios=[{"label": "Bateria", "vals": ["a", "b"], "win": 5}])
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("vencedor fora da faixa" in e for e in validacao["erros"])


def test_conteudo_com_documento_completo_reprova():
    contrato = _contrato_completo(conteudo_html=PAGINA_COMPLETA)
    contrato["conteudo_html"] = PAGINA_COMPLETA  # força o documento inteiro
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("documento completo" in e for e in validacao["erros"])


# --- Ponte com o gate por produto (M04.17A) ---------------------------------

def test_comparativo_com_evidencia_dos_dois_aprova():
    avaliacao = avaliar_contrato(_contrato_completo())
    assert avaliacao["ok"] is True, avaliacao["erros"]
    assert avaliacao["gate"]["veredito"] == "APROVADO"
    assert avaliacao["gate"]["produtos_sem_valor"] == []


def test_comparativo_com_evidencia_de_um_so_reprova():
    """A lacuna do Issue #9, vista pelo adaptador: um produto sem preço
    (e sem outra evidencia) reprova o comparativo inteiro.

    Repare nas DUAS camadas: o gate genérico (M04.17A) aprova o produto
    sem preço pelo critério `fonte_primaria` — a ficha do fabricante tem
    link. Quem reprova é a REGRA DO COMPARATIVO do adaptador, porque em
    comparativo a ficha do fabricante não é valor acrescentado. É
    exatamente por isso que a regra existe e não está no gate genérico.
    """
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
                 "Pixel 11": []}
    contrato = _contrato_completo(price_history=historico)
    avaliacao = avaliar_contrato(contrato)
    assert avaliacao["ok"] is False
    # camada 1: o gate genérico aprova (fonte_primaria do produto)
    assert avaliacao["gate"]["veredito"] == "APROVADO"
    assert "fonte_primaria" in avaliacao["gate"]["criterios_por_produto"]["Pixel 11"]
    # camada 2: a regra do comparativo reprova
    assert any("Pixel 11" in e and "comparativo" in e for e in avaliacao["erros"])


def test_contrato_para_mcp_recusa_contrato_sem_evidencia():
    historico = {"Galaxy S26": [{"data": "2026-09-17", "preco": 5999.00, "fonte": AMAZON}],
                 "Pixel 11": []}
    contrato = _contrato_completo(price_history=historico)
    try:
        contrato_para_mcp(contrato)
    except ContratoInvalido as erro:
        assert any("Pixel 11" in e for e in erro.erros)
    else:
        raise AssertionError("contrato sem evidencia por produto foi aceito")


# --- Conversão para o MCP ----------------------------------------------------

def test_parametros_do_mcp_tem_exatamente_as_chaves_do_contrato():
    params = contrato_para_mcp(_contrato_completo())
    assert set(params) == {"title", "content", "products", "notas", "buys",
                            "crits", "veredito", "cat_slug"}


def test_listas_do_mcp_ficam_alinhadas_com_os_produtos():
    params = contrato_para_mcp(_contrato_completo())
    assert params["products"] == ["Galaxy S26", "Pixel 11"]
    assert params["notas"] == [9.0, 8.5]
    assert params["buys"] == [AMAZON, ML]
    assert len(params["products"]) == len(params["notas"]) == len(params["buys"])


def test_content_do_mcp_nao_traz_documento_completo():
    params = contrato_para_mcp(_contrato_completo())
    assert "<!DOCTYPE" not in params["content"]
    assert "<html" not in params["content"].lower()
    assert "<head" not in params["content"].lower()
    assert "<h1>" in params["content"]


def test_crits_preservam_label_vals_e_vencedor():
    params = contrato_para_mcp(_contrato_completo())
    assert params["crits"][0]["label"] == "Bateria"
    assert params["crits"][0]["vals"] == ["5000 mAh", "4600 mAh"]
    assert params["crits"][0]["win"] == 0


def test_sete_criterios_sao_bloqueados_antes_do_mcp():
    """O MCP trunca em 6; o adaptador recusa em vez de deixar truncar."""
    criterios = [{"label": f"C{i}", "vals": ["a", "b"], "win": 0} for i in range(7)]
    contrato = _contrato_completo(criterios=criterios)
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("trunca em 6" in e for e in validacao["erros"])


# --- Entrada malformada: ERRO, nunca exceção -------------------------------
# Mesmo princípio do M04.17A: exceção num gate fail-closed vira passage
# indevida (ou queda) em quem chama. Achado na REVISÃO PRÉ-MERGE do PR #8.

def test_produto_que_nao_e_dicionario_reprova_sem_explodir():
    contrato = {"titulo": "A vs B", "produtos": ["Galaxy S26", {"nome": "Pixel 11"}],
                "conteudo_html": "<p>x</p>"}
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("invalido" in e for e in validacao["erros"])


def test_avaliar_contrato_com_produto_malformado_nao_explode():
    contrato = {"titulo": "A vs B", "produtos": ["Galaxy S26"], "conteudo_html": "<p>x</p>"}
    avaliacao = avaliar_contrato(contrato)
    assert avaliacao["ok"] is False
    assert avaliacao["erros"]


def test_contrato_para_mcp_com_produto_malformado_recusa():
    contrato = {"titulo": "A vs B", "produtos": ["Galaxy S26"], "conteudo_html": "<p>x</p>"}
    try:
        contrato_para_mcp(contrato, exigir_evidencia=False)
    except ContratoInvalido as erro:
        assert erro.erros
    else:
        raise AssertionError("contrato malformado foi aceito")


def test_criterio_que_nao_e_dicionario_reprova_sem_explodir():
    contrato = _contrato_completo(criterios=["Bateria"])
    validacao = validar_contrato(contrato)
    assert validacao["ok"] is False
    assert any("invalido" in e for e in validacao["erros"])
