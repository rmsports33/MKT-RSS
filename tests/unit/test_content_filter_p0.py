"""
Testes P0 — content_filter (offline, sem rede)
pytest tests/test_content_filter_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.content_filter import (
    filtrar_conteudo,
    filtrar_item_rss,
    filtrar_valor_acrescentado,
    gate_publicacao,
)


def test_tecnologia_aprovada():
    r = filtrar_conteudo("Galaxy S26 Ultra: review da câmera", "Análise de bateria e zoom 5x.")
    assert r["veredito"] == "APROVADO" and r["categorias"] == []


def test_apostas_bloqueia():
    r = filtrar_conteudo("Melhor bet com bônus", "Aposta esportiva com odd de 2.0")
    assert r["veredito"] == "BLOQUEADO" and "apostas" in r["categorias"]


def test_adulto_bloqueia_sem_acento():
    assert filtrar_conteudo("Vazou privacy de famosa", "")["veredito"] == "BLOQUEADO"


def test_politica_revisa_nao_bloqueia():
    r = filtrar_conteudo("Senado vota marco da IA", "Deputados debatem texto")
    assert r["veredito"] == "REVISAR"


def test_categoria_extra():
    r = filtrar_conteudo("Sorteio de iPhone no Instagram", "", {"sorteio": [r"sorteio"]})
    assert r["veredito"] == "BLOQUEADO"


def test_gate_rss():
    r = filtrar_item_rss({"titulo": "Novo notebook", "resumo": "Review", "link": "https://x", "fonte": "blog"})
    assert r["veredito"] == "APROVADO" and r["link"] == "https://x"


# --- Gate de VALOR acrescentado (regra 14 do AGENTS.md, 28/09/2026) ---
# Caso que ORIGINOU a regra: o post 9160 (reescrita da matéria da Canaltech)
# introduzia ZERO número novo. Aqui ele tem que BARRAR.


def test_valor_bloqueia_reescrita_de_fonte_unica():
    """Reescrita de 1 fonte de terceiro, com crédito e sem dado próprio = BLOQUEADO."""
    r = filtrar_valor_acrescentado(
        titulo="Preço alto leva 40% dos cancelamentos de Game Pass e PS Plus",
        texto="A pesquisa da Circana apontou o preço como causa dominante.",
        links=["https://canaltech.com.br/games/40-dos-cancelamentos/"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["motivo"] == "sem_valor_acrescentado"
    assert r["criterios"] == []


def test_valor_aprova_preco_com_data():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Na Amazon sai por R$ 7.191 no Pix, capturado em 17/09/2026.",
        links=["https://www.amazon.com.br/dp/B0XXX"],
    )
    assert r["veredito"] == "APROVADO" and "preco_br_data" in r["criterios"]


def test_valor_bloqueia_preco_sem_data():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Na Amazon sai por R$ 9.999,00.",
        links=["https://www.amazon.com.br/dp/B0XXX"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "preco_br_data" not in r["criterios"]


def test_valor_bloqueia_data_sem_preco():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Oferta capturada em 17/09/2026.",
        links=["https://www.amazon.com.br/dp/B0XXX"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "preco_br_data" not in r["criterios"]


def test_valor_bloqueia_preco_datado_sem_fonte_comercial():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Oferta de R$ 9.999,00 capturada em 17/09/2026.",
        links=[],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "preco_br_data" not in r["criterios"]


def test_valor_bloqueia_data_calendario_invalida():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Na Amazon sai por R$ 9.999,00, capturado em 31/02/2026.",
        links=["https://www.amazon.com.br/dp/B0XXX"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "preco_br_data" not in r["criterios"]


def test_valor_aprova_fonte_primaria_oficial():
    r = filtrar_valor_acrescentado(
        titulo="Anthropic lanza novo modelo",
        texto="Anunciado hoje.",
        links=["https://www.anthropic.com/news/claude-sonnet-5-5"],
    )
    assert r["veredito"] == "APROVADO" and "fonte_primaria" in r["criterios"]


def test_valor_nao_aceita_terceira_parte_como_primaria():
    """Matéria de terceiro sobre o anúncio NÃO é fonte primária."""
    r = filtrar_valor_acrescentado(
        titulo="Novo processador Qualcomm",
        texto="Anunciado hoje.",
        links=["https://www.theverge.com/2026/09/28/qualcomm-chip"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_valor_rejeita_blogs_tecn_que_faltavam_na_lista():
    """REGRESSÃO 28/09: sixcolors/macstories passavam como 'fonte primária' porque
    não estavam na lista de terceiros. São blogs, não o fabricante."""
    for url in ["https://sixcolors.com/post/2026/09/stolen-device-protection/",
                "https://www.macstories.net/reviews/our-favorite-indie-apps/",
                "https://liliputing.com/linux-on-snapdragon-pine-64-and-f-droid/",
                "https://news.ycombinator.com/item?id=49881850"]:
        r = filtrar_valor_acrescentado(titulo="x", texto="y", links=[url])
        assert r["veredito"] == "BLOQUEADO", f"falso positivo: {url}"


def test_valor_aceita_fabricante_real():
    """Contraprova do teste anterior: a lista é de terceiro, não trava tudo."""
    for url in ["https://www.samsung.com/br/newsroom/",
                "https://www.apple.com/newsroom/2026/09/iphone-18-pro/",
                "https://www.anthropic.com/news/claude-sonnet-5-5",
                "https://www.qualcomm.com/news/releases/2026/09"]:
        r = filtrar_valor_acrescentado(titulo="x", texto="y", links=[url])
        assert r["veredito"] == "APROVADO", f"falso negativo: {url}"


def test_valor_aprova_mediacao_propria():
    r = filtrar_valor_acrescentado(
        titulo="Testamos o Galaxy por 14 dias",
        texto="Testamos por 14 dias de uso. Medimos a bateria de 5.000 mAh: 7h12 de vídeo 4K.",
        links=[],
    )
    assert r["veredito"] == "APROVADO" and "medicao_propria" in r["criterios"]


def test_valor_nao_confunde_ficha_tecnica_com_medicao():
    """BUG real de 28/09: spec de fabricante (6,2 pol / 120 Hz / 4.000 mAh) NÃO é
    medição própria. Ficha repetida do fabricante é o caso 'Low' da SQRG 5.2.1."""
    r = filtrar_valor_acrescentado(
        titulo="Ficha técnica do aparelho",
        texto="Tela de 6,2 pol, 120 Hz, 4.000 mAh, câmera de 50 MP, 256 GB.",
        links=["https://www.samsung.com/br/produto"],
    )
    assert "medicao_propria" not in r["criterios"]
    assert r["ficha_tecnica"] is True


def test_valor_nao_confunde_medida_pt_com_mediacao():
    """'medida que foi bem recebida' significa DECISÃO, não medição."""
    r = filtrar_valor_acrescentado(
        titulo="Preço alto leva 40% dos cancelamentos",
        texto="A Nintendo anunciou redução de preços, medida que foi bem recebida pela comunidade.",
        links=["https://canaltech.com.br/games/x"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_valor_aprova_cruzamento_de_duas_fontes():
    r = filtrar_valor_acrescentado(
        titulo="S26 Ultra vs Pixel 11",
        texto="Comparamos especificações e preço.",
        links=["https://www.gsmarena.com/x", "https://www.apple.com/y"],
        tem_cruzamento=True,
    )
    assert r["veredito"] == "APROVADO" and "cruzamento_2fontes" in r["criterios"]


def test_valor_bloqueia_flag_cruzamento_com_uma_fonte():
    r = filtrar_valor_acrescentado(
        titulo="S26 Ultra vs Pixel 11",
        texto="Comparativo sem evidência independente.",
        links=["https://www.gsmarena.com/x"],
        tem_cruzamento=True,
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "cruzamento_2fontes" not in r["criterios"]


def test_valor_bloqueia_duas_urls_do_mesmo_dominio():
    r = filtrar_valor_acrescentado(
        titulo="S26 Ultra vs Pixel 11",
        texto="Comparativo sem segunda fonte independente.",
        links=["https://www.gsmarena.com/x", "https://m.gsmarena.com/y"],
        tem_cruzamento=True,
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "cruzamento_2fontes" not in r["criterios"]


def test_valor_bloqueia_duas_fontes_sem_declarar_cruzamento():
    r = filtrar_valor_acrescentado(
        titulo="S26 Ultra vs Pixel 11",
        texto="Duas referências não provam comparação explícita.",
        links=["https://www.gsmarena.com/x", "https://www.theverge.com/y"],
        tem_cruzamento=False,
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "cruzamento_2fontes" not in r["criterios"]


def test_valor_rotula_video_separado_de_medicao():
    """Vídeo e medição são sinais diferentes — o relatório precisa distinguir."""
    r = filtrar_valor_acrescentado(
        titulo="Review do Galaxy S26",
        texto="Análise do aparelho.",
        links=[],
        tem_video=True,
    )
    assert r["veredito"] == "APROVADO"
    assert "video_transcrito" in r["criterios"]
    assert "medicao_propria" not in r["criterios"]


def test_valor_uma_fonte_so_nao_e_cruzamento():
    """1 link não é cruzamento — tem que ser 2+."""
    r = filtrar_valor_acrescentado(
        titulo="Notícia qualquer",
        texto="Sem nada próprio.",
        links=["https://www.gsmarena.com/unicos-noticia"],
    )
    assert r["veredito"] == "BLOQUEADO"


# --- M04.16: falha 4 (default-allow de fonte primária) ---
# Antes, "se não é veículo conhecido, é primário". Qualquer domínio inventado
# virava fonte primária e o gate aprovava tudo. Agora a lista é positiva.


def test_valor_bloqueia_dominio_desconhecido_como_primaria():
    r = filtrar_valor_acrescentado(
        titulo="Notícia qualquer",
        texto="Sem nada próprio.",
        links=["https://blog-qualquer.example/post"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert "fonte_primaria" not in r["criterios"]


def test_valor_link_desconhecido_nao_salva_preco_sem_data():
    """Regressão da regressão: link qualquer não pode ressuscitar o fail-open."""
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Oferta por R$ 9.999,00.",
        links=["https://blog-qualquer.example/post"],
    )
    assert r["veredito"] == "BLOQUEADO"
    assert r["criterios"] == []


def test_valor_bloqueia_dominio_disfarcado_de_marketplace():
    for url in [
        "https://amazon.com.br.evil.example/dp/B0XXX",
        "https://notamazon.example/amazon.com.br",
    ]:
        r = filtrar_valor_acrescentado(
            titulo="Galaxy S26 Ultra",
            texto="Oferta de R$ 9.999,00 em 17/09/2026.",
            links=[url],
        )
        assert r["veredito"] == "BLOQUEADO", f"bypass aceito: {url}"


def test_valor_bloqueia_dominio_disfarcado_de_fabricante():
    r = filtrar_valor_acrescentado(
        titulo="Anúncio oficial",
        texto="Anunciado hoje.",
        links=["https://samsung.com.evil.example/news/x"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_valor_aceita_subdominio_de_fabricante():
    for url in ["https://br.samsung.com/news/x", "https://www.apple.com/newsroom/2026/09/iphone/"]:
        r = filtrar_valor_acrescentado(titulo="x", texto="y", links=[url])
        assert r["veredito"] == "APROVADO", f"falso negativo: {url}"


def test_valor_aceita_fonte_oficial_por_formato():
    for url in [
        "https://www.gov.br/anatel/pt-br/noticias/x",
        "https://www.ifsp.edu.br/estudo/x",
        "https://news.mit.edu/2026/estudo.pdf",
        "https://arxiv.org/abs/2609.00001",
        "https://doi.org/10.1000/xyz",
        "https://www.inmetro.gov.br/legislacao/portaria.pdf",
    ]:
        r = filtrar_valor_acrescentado(titulo="x", texto="y", links=[url])
        assert r["veredito"] == "APROVADO", f"falso negativo: {url}"


def test_valor_nao_aceita_pdf_em_dominio_de_terceiro():
    r = filtrar_valor_acrescentado(
        titulo="x",
        texto="y",
        links=["https://canaltech.com.br/materia.pdf"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_valor_nao_aceita_pdf_na_query():
    r = filtrar_valor_acrescentado(
        titulo="x",
        texto="y",
        links=["https://blog-qualquer.example/redirect?file=doc.pdf"],
    )
    assert r["veredito"] == "BLOQUEADO"


def test_valor_rejeita_url_sem_http():
    for url in ["javascript:alert(1)", "//www.amazon.com.br/dp/X", "ftp://amazon.com.br/x"]:
        r = filtrar_valor_acrescentado(
            titulo="Galaxy",
            texto="Oferta de R$ 9.999,00 em 17/09/2026.",
            links=[url],
        )
        assert r["veredito"] == "BLOQUEADO", f"aceitou esquema inválido: {url}"


def test_valor_aceita_url_maiuscula_de_marketplace():
    r = filtrar_valor_acrescentado(
        titulo="Galaxy S26 Ultra",
        texto="Oferta de R$ 9.999,00 em 17/09/2026.",
        links=["HTTPS://WWW.AMAZON.COM.BR/dp/B0XXX"],
    )
    assert r["veredito"] == "APROVADO"
    assert "preco_br_data" in r["criterios"]


def test_gate_publicacao_compliance_tem_precedencia():
    """Apostas bloqueiam mesmo com valor acrescentado presente."""
    r = gate_publicacao(
        titulo="Casino bonus 100 free spins",
        texto="R$ 1.234,56 em 17/09/2026",
    )
    assert r["veredito"] == "BLOQUEADO" and "apostas" in r["categorias"]


def test_gate_publicacao_revisar_passa_com_valor():
    """Notícia política é REVISAR (humano decide), mas com valor é publicável."""
    r = gate_publicacao(
        titulo="Senado vota marco da IA",
        texto="Preço de referência R$ 9.999,00 em 17/09/2026.",
        links=["https://www.amazon.com.br/dp/B0XXX"],
    )
    assert r["veredito"] == "REVISAR"
    assert r["criterios_valor"] == ["preco_br_data"]
