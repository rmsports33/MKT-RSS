"""Contraprovas fail-closed do revisor editorial unico, sem WordPress real."""
import copy
import re
import unittest

from mkt_flow_p0.revisor_qualidade_unico import (
    VERSAO, _sha, avaliar_artigo, verificar_versao,
)


def artigo():
    return {
        "id": 9768, "status": "draft",
        "title": "Android MCP: como agentes de IA vao conectar aplicativos",
        "slug": "android-mcp-agentes-ia-conectar-aplicativos",
        "excerpt": "Google apresenta o Android MCP e detalha os limites para o uso de agentes de inteligencia artificial em aplicativos.",
        "content": (
            "<p>Google apresentou um recurso experimental sem disponibilidade geral.</p>"
            + "<p>Exemplo explicado com contexto e cautela sobre condicoes atuais.</p>" * 80
            + '<p><a href="https://developer.android.com/ai/appfunctions">AppFunctions</a></p>'
            + '<a href="https://conexotech.com.br/android-drop-recursos-como-conferir/">Android</a>'
            + '<a href="https://conexotech.com.br/microsoft-ia-altera-falas-labios-video-ao-vivo/">IA</a>'
            + '<a href="https://conexotech.com.br/ceo-da-anthropic-pede-freio-na-ia-e-alerta-risco-online/">Seguranca</a>'
        ),
        "categories": [10], "featured_media": 9714,
    }


def media():
    return {"id": 9714, "alt_text": "Smartphone Android com apps",
            "description": "Fonte individual Pexels; https://www.pexels.com/license/"}


def fontes():
    return [{"url": "https://developer.android.com/ai/appfunctions",
             "verificada": True, "alegacoes": ["Disponibilidade experimental"]}]


def evidencias(post):
    fp = _sha(post)
    return {k: {"fingerprint": fp, "reviewer": "editor-independente",
                "aprovado": True, "referencias": ["https://evidencias.example.org/registro"]}
            for k in ("licenca_imagem", "revisao_substantiva", "visual_390", "visual_1440",
                      "alegacoes", "links_internos")}


class TestRevisorUnico(unittest.TestCase):
    def test_sem_evidencias_nao_aprova(self):
        r = avaliar_artigo(artigo(), media=media(), fontes=fontes())
        self.assertEqual(r["schema"], VERSAO)
        self.assertEqual(r["veredito"], "REVISAO_NECESSARIA")
        self.assertIn("licenca_imagem", r["pendencias"])
        self.assertIn("revisao_substantiva", r["pendencias"])
        self.assertFalse(r["publicacao_autorizada"])

    def test_evidencias_completas_e_fonte_confrontada(self):
        p = artigo()
        r = avaliar_artigo(p, media=media(), fontes=fontes(),
                           evidencias=evidencias(p),
                           corpo_original_fonte="Google apresentou um recurso experimental sem disponibilidade geral.")
        self.assertEqual(r["veredito"], "APTO_PARA_APROVACAO")
        self.assertFalse(r["publicacao_autorizada"])
        self.assertTrue(verificar_versao(r, p))

    def test_conteudo_alterado_invalida_todas_as_evidencias(self):
        p = artigo()
        antes = avaliar_artigo(p, media=media(), fontes=fontes(),
                               evidencias=evidencias(p),
                               corpo_original_fonte="Google apresentou um recurso experimental sem disponibilidade geral.")
        alterado = copy.deepcopy(p)
        alterado["content"] += "<p>Trecho posterior</p>"
        self.assertFalse(verificar_versao(antes, alterado))
        novo = avaliar_artigo(alterado, media=media(), fontes=fontes(),
                              evidencias=evidencias(p))
        self.assertIn("visual_390", novo["pendencias"])
        self.assertIn("revisao_substantiva", novo["pendencias"])

    def test_sem_licenca_capa_e_categoria_reprova(self):
        p = artigo()
        p["featured_media"] = 0
        p["categories"] = [1]
        r = avaliar_artigo(p, media=media(), fontes=fontes())
        self.assertEqual(r["veredito"], "BLOQUEADO")
        self.assertTrue({"capa", "categoria", "licenca_imagem"} <= set(r["bloqueios"]))

    def test_revisor_humano_nao_pode_ser_vazio(self):
        p = artigo()
        ev = evidencias(p)
        ev["revisao_substantiva"]["reviewer"] = ""
        r = avaliar_artigo(p, media=media(), fontes=fontes(), evidencias=ev)
        self.assertIn("revisao_substantiva", r["pendencias"])

    def test_fontes_nao_evidenciadas_nao_passam(self):
        p = artigo()
        r = avaliar_artigo(p, media=media(), fontes=[{"url": "https://invalido.example.org", "verificada": True, "alegacoes": ["x"]}])
        self.assertIn("fontes", r["pendencias"])

    def test_placeholder_bloqueia(self):
        p = artigo()
        p["content"] += "<p>[LINK AFILIADO]</p>"
        r = avaliar_artigo(p, media=media(), fontes=fontes())
        self.assertIn("html", r["bloqueios"])

    def test_alegacao_propria_sem_fonte_bloqueia(self):
        p = artigo()
        p["content"] += "<p>Em nossos testes descobrimos algo.</p>"
        r = avaliar_artigo(p, media=media(), fontes=fontes(),
                           corpo_original_fonte="Google anunciou um recurso experimental.")
        self.assertIn("alegacoes", r["bloqueios"])

    def test_nao_inferir_licenca_apenas_de_media_presente(self):
        p = artigo()
        m = media()
        m["description"] = "Imagem de origem desconhecida"
        r = avaliar_artigo(p, media=m, fontes=fontes())
        self.assertIn("licenca_imagem", r["bloqueios"])

    def test_sem_alertas_numericos_nao_equivale_a_checagem_factual_humana(self):
        p = artigo()
        e = evidencias(p)
        e.pop("alegacoes")
        report = avaliar_artigo(p, media=media(), fontes=fontes(), evidencias=e,
                                corpo_original_fonte="Google apresentou um recurso experimental sem disponibilidade geral.")
        self.assertEqual(report["checks"]["alegacoes"]["estado"], "NAO_VERIFICADO")
        self.assertIn("alegacoes", report["pendencias"])
        self.assertNotEqual(report["veredito"], "APTO_PARA_APROVACAO")

    def test_ate_tres_links_nao_cria_quota_obrigatoria(self):
        p = artigo()
        # Remove os três hiperlinks do site, preservando fonte externa.
        p["content"] = re.sub(r'<a href="https://conexotech.com.br/[^"]+">[^<]+</a>', "", p["content"])
        e = evidencias(p)
        report = avaliar_artigo(p, media=media(), fontes=fontes(), evidencias=e,
                                corpo_original_fonte="Google apresentou um recurso experimental sem disponibilidade geral.")
        self.assertEqual(report["checks"]["links_internos"]["estado"], "VERIFICADO")
        self.assertNotIn("links_internos", report["pendencias"])

    def test_link_extra_violates_max_three_even_with_attestation(self):
        p = artigo()
        p["content"] += '<a href="https://conexotech.com.br/quarto-artigo/">Outro</a>'
        report = avaliar_artigo(p, media=media(), fontes=fontes(), evidencias=evidencias(p))
        self.assertEqual(report["checks"]["links_internos"]["estado"], "REPROVADO")
        self.assertIn("links_internos", report["bloqueios"])

    def test_nao_muta_snapshot(self):
        p = artigo()
        old = copy.deepcopy(p)
        avaliar_artigo(p, media=media(), fontes=fontes())
        self.assertEqual(p, old)


if __name__ == "__main__":
    unittest.main()
