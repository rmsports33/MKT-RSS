"""M04.17A — validação de evidência POR PRODUTO (regra 14, Issue #9).

A lacuna que este arquivo fecha: o gate olhava o TEXTO INTEIRO, então um
único preço com data no texto approveva um comparativo de vários produtos.
Comparativo "Galaxy S26 vs Pixel 11" com o preço só do S26 passava com
`preco_br_data`.

A regra nova: **evidência de um produto nunca aprova outro**. Cada produto é
avaliado isoladamente e TODOS precisam ter valor próprio.

Rodar:  python -m pytest tests/unit/test_content_filter_produto_p0.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mkt_flow_p0.content_filter import (  # noqa: E402
    filtrar_valor_acrescentado,
    gate_publicacao,
)

AMAZON = "https://www.amazon.com.br/dp/B0XXX"
SAMSUNG = "https://news.samsung.com/br/galaxy-s26"
PIXEL = "https://store.google.com/pt/product/pixel_11"
# Preço só vale com link de MARKETPLACE conhecido. A loja oficial do Google
# é fonte primária, não marketplace — por isso o preço do Pixel abaixo usa o
# Mercado Livre.
PIXEL_MERCADO = "https://www.mercadolivre.com.br/pixel-11/p/MLB123"


def _produto_preco(nome, preco, data, link=AMAZON):
    return {"nome": nome, "preco": preco, "data_captura": data, "fonte_preco": link}


# --- A regressão central ---------------------------------------------------

def test_comparativo_com_preco_de_um_so_e_bloqueado():
    """O defeito original: preço do S26 não pode aprovar o Pixel 11."""
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 vs Pixel 11",
        texto="O S26 sai por R$ 5.999,00 em 17/09/2026. O Pixel 11 ainda sem preço.",
        produtos=[
            _produto_preco("Galaxy S26", "R$ 5.999,00", "17/09/2026"),
            {"nome": "Pixel 11"},
        ],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["motivo"] == "produto_sem_valor"
    assert r["produtos_sem_valor"] == ["Pixel 11"]


def test_comparativo_com_preco_dos_dois_aprova():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 vs Pixel 11",
        texto="Preços capturados em 17/09/2026.",
        produtos=[
            _produto_preco("Galaxy S26", "R$ 5.999,00", "17/09/2026"),
            _produto_preco("Pixel 11", "R$ 4.299,00", "17/09/2026", PIXEL_MERCADO),
        ],
    )
    assert r["veredito"] == "APROVADO"
    assert r["motivo"] == "valor_acrescentado_por_produto"
    assert r["produtos_sem_valor"] == []
    assert r["criterios_por_produto"]["Galaxy S26"] == ["preco_br_data"]
    assert r["criterios_por_produto"]["Pixel 11"] == ["preco_br_data"]


def test_preco_com_loja_oficial_nao_conta_como_preco_mercado():
    """Contraprova: preço exige MARKETPLACE. Loja oficial é fonte primária."""
    r = filtrar_valor_acrescentado(
        titulo="Pixel 11",
        texto="Preço na loja oficial.",
        produtos=[_produto_preco("Pixel 11", "R$ 4.299,00", "17/09/2026", PIXEL)],
    )
    assert r["veredito"] == "APROVADO"
    # Aprovado pela fonte primária (loja oficial), NÃO pelo preço.
    assert r["criterios_por_produto"]["Pixel 11"] == ["fonte_primaria"]


def test_preco_no_texto_geral_nao_salva_produto_sem_evidencia():
    """Contaminação pelo texto: o preço geral não pode aprovar ninguém."""
    r = filtrar_valor_acrescentado(
        titulo="Comparativo",
        texto="Sai por R$ 5.999,00 em 17/09/2026 (link da Amazon).",
        links=[AMAZON],
        produtos=[
            {"nome": "Produto A"},
            {"nome": "Produto B"},
        ],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["produtos_sem_valor"] == ["Produto A", "Produto B"]


def test_evidencia_de_um_produto_nao_aprova_outro():
    """Vídeo transcrito do produto A não aprova o produto B."""
    r = filtrar_valor_acrescentado(
        titulo="Comparativo",
        texto="Analisamos os dois.",
        produtos=[
            {"nome": "Produto A",
             "evidencia_video": {"url": "https://www.youtube.com/watch?v=abc123",
                                  "transcricao": " ".join(["palavra"] * 80)}},
            {"nome": "Produto B"},
        ],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["produtos_sem_valor"] == ["Produto B"]
    assert "video_transcrito" in r["criterios_por_produto"]["Produto A"]


def test_marketplace_de_um_produto_nao_da_preco_ao_outro():
    r = filtrar_valor_acrescentado(
        titulo="Comparativo",
        texto="Comparamos.",
        produtos=[
            _produto_preco("Produto A", "R$ 5.999,00", "17/09/2026", AMAZON),
            {"nome": "Produto B", "links": [AMAZON]},
        ],
    )
    assert r["veredito"] == "BLOQUEADO"
    # Produto B tem o link do marketplace, mas não tem preço próprio.
    assert "preco_br_data" not in r["criterios_por_produto"]["Produto B"]


# --- Evidência individual de cada produto ---------------------------------

def test_produto_com_fonte_primaria_propria_aprova():
    r = filtrar_valor_acrescentado(
        titulo="Anúncio",
        texto="Anunciado hoje.",
        produtos=[{"nome": "Galaxy S26", "links": [SAMSUNG]}],
    )
    assert r["veredito"] == "APROVADO"
    assert r["criterios_por_produto"]["Galaxy S26"] == ["fonte_primaria"]


def test_produto_com_medicao_propria_aprova():
    r = filtrar_valor_acrescentado(
        titulo="Testamos o Galaxy",
        texto="Medimos a bateria.",
        produtos=[{
            "nome": "Galaxy S26",
            "evidencia_medicao": {
                "metodo": "Loop de vídeo 4K, brilho 200 nits",
                "medicoes": [{"metrica": "video4k", "valor": 7.2, "unidade": "h"},
                             {"metrica": "misto", "valor": 11.4, "unidade": "h"}],
            },
        }],
    )
    assert r["veredito"] == "APROVADO"
    assert "medicao_propria" in r["criterios_por_produto"]["Galaxy S26"]


def test_produto_com_cruzamento_proprio_aprova():
    r = filtrar_valor_acrescentado(
        titulo="S26 vs Pixel",
        texto="Comparamos os dois.",
        produtos=[{
            "nome": "S26",
            "links": ["https://www.gsmarena.com/x", "https://www.apple.com/y"],
            "tem_cruzamento": True,
        }],
    )
    assert r["veredito"] == "APROVADO"
    assert "cruzamento_2fontes" in r["criterios_por_produto"]["S26"]


def test_cruzamento_de_um_produto_nao_cruza_outro():
    r = filtrar_valor_acrescentado(
        titulo="Comparativo",
        texto="Comparamos.",
        produtos=[
            {"nome": "A", "links": ["https://www.gsmarena.com/x", "https://www.apple.com/y"],
             "tem_cruzamento": True},
            {"nome": "B"},
        ],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["produtos_sem_valor"] == ["B"]


# --- Falha fechada em cada ponto -------------------------------------------

def test_data_invalida_do_produto_nao_conta():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy",
        texto="Oferta.",
        produtos=[_produto_preco("Galaxy S26", "R$ 5.999,00", "31/02/2026")],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "preco_br_data" not in r["criterios_por_produto"].get("Galaxy S26", [])


def test_preco_sem_marketplace_no_produto_nao_aprova_por_preco():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy",
        texto="Oferta.",
        produtos=[_produto_preco("Galaxy S26", "R$ 5.999,00", "17/09/2026",
                                  link="https://blog-qualquer.example/post")],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_produto_invalido_nao_aprova():
    r = filtrar_valor_acrescentado(
        titulo="x", texto="y", produtos=["não é dicionário"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_exigir_produtos_sem_lista_bloqueia():
    """Fluxo comparativo: sem lista de produtos, não há como validar."""
    r = filtrar_valor_acrescentado(
        titulo="Comparativo", texto="Com preço e data.",
        links=[AMAZON], exigir_produtos=True,
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["motivo"] == "produtos_ausentes"


def test_exigir_produtos_com_lista_vazia_bloqueia():
    r = filtrar_valor_acrescentado(
        titulo="Comparativo", texto="x", produtos=[], exigir_produtos=True,
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["motivo"] == "produtos_ausentes"


# --- Metadados do modo ------------------------------------------------------

def test_modo_texto_declara_que_por_produto_nao_foi_aplicado():
    """A lacuna fica VISÍVEL: quem chamar sem produtos vê que não validou."""
    r = filtrar_valor_acrescentado(
        titulo="Galaxy", texto="R$ 5.999,00 em 17/09/2026", links=[AMAZON],
    )
    assert r["evidencia_por_produto"] == "nao_aplicada"


def test_modo_por_produto_declara_que_foi_aplicado():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy", texto="x",
        produtos=[_produto_preco("Galaxy S26", "R$ 5.999,00", "17/09/2026")],
    )
    assert r["evidencia_por_produto"] == "aplicada"


def test_gate_publicacao_repassa_produtos_e_motivo():
    r = gate_publicacao(
        titulo="Comparativo", texto="x",
        produtos=[{"nome": "A"}, {"nome": "B"}],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["motivo"] == "produto_sem_valor"
    assert r["produtos_sem_valor"] == ["A", "B"]
    assert r["evidencia_por_produto"] == "aplicada"


def test_produto_sem_nome_usa_identificador_de_fallback():
    r = filtrar_valor_acrescentado(
        titulo="x", texto="y", produtos=[{"preco": "R$ 1,00", "data_captura": "17/09/2026"}],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["produtos_sem_valor"] == ["produto #1"]


def test_avisos_por_produto_nao_sumem():
    """Declaração não comprovada de um produto aparece nomeada."""
    r = filtrar_valor_acrescentado(
        titulo="x", texto="y",
        produtos=[{"nome": "A", "tem_cruzamento": True, "links": ["https://www.gsmarena.com/x"]}],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert any(a.startswith("[A]") for a in r["avisos"])


# --- Compatibilidade com o contrato legado M04.16C -------------------------
# O M04.17A é aditivo. Esta trava roda SEMPRE (no CI): se alguém mudar o
# contrato legado, o CI reprova. A comparação completa contra a implementação
# antiga está em tools/2026-10-21_compatibilidade_m0416c.py (precisa do
# arquivo da versão anterior, que não existe no master).

CHAVES_LEGADAS_M0416C = {
    "veredito", "criterios", "total_criterios", "motivo",
    "ficha_tecnica", "aviso", "avisos",
}


def test_contrato_legado_preserva_todas_as_chaves():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy", texto="R$ 5.999,00 em 17/09/2026", links=[AMAZON],
    )
    assert CHAVES_LEGADAS_M0416C.issubset(set(r.keys()))
    # A única chave nova é a que declara o modo por produto.
    assert set(r.keys()) - CHAVES_LEGADAS_M0416C == {"evidencia_por_produto"}


def test_contrato_legado_aceita_chamada_posicional_antiga():
    """A assinatura M04.16C (posicional) continua válida."""
    r = filtrar_valor_acrescentado(
        "Galaxy", "R$ 5.999,00 em 17/09/2026", [AMAZON], False, False, False,
        None, None, None,
    )
    assert r["veredito"] == "APROVADO"
    assert r["criterios"] == ["preco_br_data"]


def test_gate_publicacao_legado_preserva_chaves():
    # `gate_publicacao` devolve a FUSAO do compliance com o valor, entao o
    # conjunto legado de chaves e' outro (nao o de filtrar_valor_acrescentado).
    legado_gate = {"veredito", "categorias", "trechos", "total_sinais",
                   "criterios_valor", "avisos_valor"}
    r = gate_publicacao(
        titulo="Galaxy", texto="R$ 5.999,00 em 17/09/2026", links=[AMAZON],
    )
    assert legado_gate.issubset(set(r.keys()))
    novas = set(r.keys()) - legado_gate
    assert novas == {"evidencia_por_produto", "criterios_por_produto", "produtos_sem_valor"}
    assert r["criterios_valor"] == ["preco_br_data"]
    assert r["avisos_valor"] == []
    assert r["evidencia_por_produto"] == "nao_aplicada"
