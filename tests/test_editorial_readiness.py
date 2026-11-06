"""Prontidao editorial nao e permissao de publicacao.

Sem acesso a rede, imagem ou WordPress. O fluxo de rascunho permanece viavel.
"""
import copy

from mkt_flow_p0.editorial_identity import criar_handoff_chatgpt
from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial


SOURCE = "https://example.org/pauta"
EXTRA = {"sources": [{"name": "Fonte oficial", "url": "https://www.example.com/detalhes",
                       "facts": ["A documentacao informa a disponibilidade do recurso citado."]}]}
DESCRIPTION = "O recurso anunciado pelo fabricante sera analisado a partir da documentacao e de informacoes complementares de uso real no Brasil."
HTML = ('<h2>O que mudou</h2><p>Contexto</p><h2>Impactos</h2>'
        '<a href="https://conexotech.com.br/android-drop-recursos-como-conferir/">Android</a>'
        '<a href="https://conexotech.com.br/ssd-sata-ou-nvme-como-escolher/">SSD</a>'
        '<a href="https://conexotech.com.br/hdmi-arc-soundbar-tv-como-conectar/">HDMI</a>')


def packet(extended=False):
    text = ("## Fatos confirmados\n\n" + "A pauta depende de dados comprovados e de contexto brasileiro. " *
            (72 if extended else 25) + "\n\n## Por que importa\n\n" +
            ("A explicacao adicional preserva as fontes e evita repeticoes. " * (8 if extended else 4)))
    data = {"titulo_seo": "Android e as novas funcoes de assistentes",
            "meta_description": DESCRIPTION,
            "slug": "android-assistentes-funcoes", "texto_markdown": text}
    return criar_handoff_chatgpt(data, url_fonte=SOURCE, fonte_nome="Noticiario",
                                 contexto_complementar=EXTRA if extended else None)


def test_short_single_source_draft_is_flagged_not_published():
    r = avaliar_prontidao_editorial(packet(), html="<h2>Resumo</h2>")
    assert r["status"] == "ENRIQUECIMENTO_PENDENTE"
    assert "pesquisa_multifonte_pendente" in r["pendencias"]
    assert "tres_links_internos_pendentes" in r["pendencias"]
    assert "imagem_destacada_com_direitos_pendente" in r["pendencias"]
    assert r["pronto_para_publicar"] is False


def test_full_pack_is_ready_only_for_human_review():
    r = avaliar_prontidao_editorial(packet(True), html=HTML,
                                    featured_media_id=9714,
                                    direitos_imagem_confirmados=True)
    assert r["status"] == "PRONTO_PARA_REVISAO_HUMANA"
    assert r["pendencias"] == []
    assert r["links_internos"] == 3
    assert r["fontes"] == 2
    assert r["pronto_para_publicar"] is False


def test_media_id_without_rights_is_not_accepted():
    r = avaliar_prontidao_editorial(packet(True), html=HTML, featured_media_id=9714)
    assert "imagem_destacada_com_direitos_pendente" in r["pendencias"]


def test_external_and_fabricated_links_do_not_count():
    html = '<h2>Inicio</h2><h2>Mais</h2>' + (
        '<a href="https://fake-conexotech.com.br/teste">nao</a>'
        '<a href="javascript:alert(1)">nao</a>'
        '<a href="https://conexotech.com.br/">home</a>')
    r = avaliar_prontidao_editorial(packet(True), html=html,
                                    featured_media_id=9714,
                                    direitos_imagem_confirmados=True)
    assert r["links_internos"] == 0
    assert "tres_links_internos_pendentes" in r["pendencias"]


def test_tampered_handoff_cannot_pass_quality_gate():
    h = copy.deepcopy(packet(True))
    h["markdown"] += " texto modificado fora do hash"
    r = avaliar_prontidao_editorial(h, html=HTML,
                                    featured_media_id=9714,
                                    direitos_imagem_confirmados=True)
    assert r["status"] == "PACOTE_INVALIDO"
    assert r["pronto_para_publicar"] is False


def test_short_news_can_be_labeled_brief_but_not_auto_published():
    r = avaliar_prontidao_editorial(packet(), genero="nota_breve", html="<h2>Resumo</h2>")
    assert r["status"] == "ENRIQUECIMENTO_PENDENTE"
    assert r["pronto_para_publicar"] is False


def test_unsupported_genre_defaults_to_news():
    r = avaliar_prontidao_editorial(packet(True), genero="faz_de_conta", html=HTML,
                                    featured_media_id=9714,
                                    direitos_imagem_confirmados=True)
    assert r["genero"] == "noticia"


def test_rss_excerpt_is_candidate_not_multisource_verification():
    """A promising second RSS link does not certify independent corroboration."""
    article = {"titulo_seo": "Android e assistentes de IA", 
               "meta_description": DESCRIPTION, "slug": "android-assistentes-de-ia",
               "texto_markdown": packet(True)["markdown"]}
    rss = {"sources": [
        {"name": "Canaltech (RSS pendente de apuração)",
         "url": "https://canaltech.com.br/android/candidato/",
         "facts": ["Resumo de RSS (alegações NÃO verificadas): O novo sistema adiciona recursos."]}]}
    handoff = criar_handoff_chatgpt(article, url_fonte=SOURCE,
                                    fonte_nome="Noticiário", contexto_complementar=rss)
    report = avaliar_prontidao_editorial(
        handoff, html=HTML, featured_media_id=9714,
        direitos_imagem_confirmados=True)
    assert report["fontes"] == 2
    assert report["fontes_rss_pendentes"] == 1
    assert report["status"] == "ENRIQUECIMENTO_PENDENTE"
    assert "pesquisa_multifonte_pendente" in report["pendencias"]
    assert "fontes_rss_candidatas_sem_verificacao" in report["pendencias"]
    assert report["pronto_para_publicar"] is False
