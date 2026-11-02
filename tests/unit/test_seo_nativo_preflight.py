"""SEO nativo do artigo WordPress — sem chamadas de rede e sem exigir <head>."""
import unittest
from unittest.mock import patch, MagicMock

from mkt_flow_p0.seo import validar_artigo_wordpress
from mkt_flow_p0.wp_publisher import publicar_no_wordpress

TITLE = "Como escolher um smartphone no Brasil em 2026"
BODY = (
    "<h2>Critérios</h2><p>" + ("Texto explicativo com informações verificadas. " * 65)
    + '</p><img src="capa.jpg" alt="Smartphone">'
    + '<a href="/reviews/galaxy/">Review</a>'
    + '<a href="/comparativos/">Comparativos</a>'
    + '<a href="https://conexotech.com.br/category/guias/">Guias</a>'
)

class SEOEditorialNativoTests(unittest.TestCase):
    def test_fragmento_wp_sem_head_apto(self):
        r = validar_artigo_wordpress(TITLE, BODY)
        self.assertEqual(r["status"], "SEM_ALERTAS")
        self.assertEqual(r["imagens_sem_alt"], 0)
        self.assertEqual(r["links_internos"], 3)
        self.assertFalse(any("canonical" in a or "description" in a for a in r["avisos"]))

    def test_avisa_sem_bloquear(self):
        r = validar_artigo_wordpress("T", '<p>Curto</p><img src="x">')
        self.assertEqual(r["status"], "REVISAR")
        self.assertIn("imagem_sem_alt", r["avisos"])
        self.assertIn("menos_de_tres_links_internos", r["avisos"])

    def test_capa_destacada_conta_como_imagem(self):
        r = validar_artigo_wordpress(TITLE, BODY.replace('<img src="capa.jpg" alt="Smartphone">', ""),
                                      tem_capa=True)
        self.assertNotIn("sem_imagem", r["avisos"])

    def test_link_malformado_nao_impede(self):
        r = validar_artigo_wordpress(TITLE, BODY + '<a href="http://[invalid">link</a>')
        self.assertEqual(r["status"], "SEM_ALERTAS")

    def test_publicador_retorna_preflight_sem_mudar_gate(self):
        mock = MagicMock(status_code=201)
        mock.json.return_value = {"id": 22, "status": "draft", "link": "https://conexotech.com.br/?p=22"}
        with patch("mkt_flow_p0.wp_publisher.requests.post", return_value=mock):
            r = publicar_no_wordpress(TITLE, "<p>Curto</p>", "UNKNOWN",
                                     "https://conexotech.com.br", "editor", "senha",
                                     status_desejado="draft")
        self.assertEqual(r["status"], "draft")
        self.assertEqual(r["seo_preflight"]["status"], "REVISAR")

    def test_gate_editorial_continua_bloqueando_publicacao(self):
        with patch("mkt_flow_p0.wp_publisher.requests.post") as send:
            r = publicar_no_wordpress(TITLE, BODY, "UNKNOWN",
                                     "https://conexotech.com.br", "editor", "senha",
                                     status_desejado="publish")
        self.assertIn("erro", r)
        send.assert_not_called()

if __name__ == "__main__":
    unittest.main()
