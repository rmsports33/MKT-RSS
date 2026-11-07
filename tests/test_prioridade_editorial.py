"""Testes offline da nota 1..10 e da integração na fila existente."""
import tempfile
import unittest
from datetime import date
from pathlib import Path

from mkt_flow_p0 import fila_pautas as fila
from mkt_flow_p0.prioridade_editorial import (
    PESOS, avaliar_pauta, calcular_nota, sugerir_criterios,
)


class TestNotaEditorial(unittest.TestCase):
    def test_pesos_totalizam_cem(self):
        self.assertEqual(sum(PESOS.values()), 100)

    def test_extremos_e_regras_de_arredondamento(self):
        self.assertEqual(calcular_nota({k: 1 for k in PESOS})["nota"], 1)
        self.assertEqual(calcular_nota({k: 10 for k in PESOS})["nota"], 10)
        self.assertEqual(calcular_nota({
            "afinidade": 10, "publico_brasileiro": 8, "utilidade": 7,
            "atualidade": 6, "evergreen": 8,
        })["nota"], 8)

    def test_recusa_criterios_incompletos_ou_enganosos(self):
        with self.assertRaises(ValueError):
            calcular_nota({"afinidade": 8})
        for value in (0, 11, True, "9", 8.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calcular_nota({k: value for k in PESOS})

    def test_heuristica_tem_proveniencia_e_nao_autoriza_publicacao(self):
        r = avaliar_pauta({"titulo": "Como proteger o celular Android no Brasil",
                          "published": "2026-11-05"},
                         referencia=date(2026, 11, 6))
        self.assertEqual(r["origem"], "HEURISTICA_PROVISORIA")
        self.assertFalse(r["audiencia_medida"])
        self.assertFalse(r["publicacao_autorizada"])
        self.assertTrue(1 <= r["nota"] <= 10)

    def test_oferta_antiga_nao_retem_recencia(self):
        item = {"titulo": "Oferta de notebook Samsung com cupom de desconto",
                "published": "2026-10-05"}
        dados = sugerir_criterios(item, referencia=date(2026, 11, 6))
        self.assertEqual(dados["atualidade"], 1)
        self.assertEqual(dados["evergreen"], 2)

    def test_data_futura_nao_significa_noticia_recente(self):
        dados = sugerir_criterios(
            {"titulo": "Novo Android anunciado", "published": "2027-01-01"},
            referencia=date(2026, 11, 6))
        self.assertEqual(dados["atualidade"], 4)

    def test_teste_sintetico_recebe_menor_nota(self):
        r = avaliar_pauta({"titulo": "[TESTE NAO PUBLICAR] pauta sintética"})
        self.assertEqual(r["nota"], 1)

    def test_criterios_humanos_sem_confundir_audiencia(self):
        r = avaliar_pauta({"titulo": "Qual TV comprar?"}, criterios={k: 8 for k in PESOS})
        self.assertEqual(r["nota"], 8)
        self.assertEqual(r["origem"], "REVISAO_EDITORIAL")
        self.assertFalse(r["audiencia_medida"])


class TestFilaComNotas(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "fila.sqlite"
        self.item = {"link": "https://example.org/primeira",
                     "titulo": "Guia de notebook no Brasil",
                     "published": "2026-11-05"}

    def tearDown(self):
        self.temp.cleanup()

    def test_fila_lista_nota_sem_persistencia_extra_obrigatoria(self):
        registrado = fila.registrar(self.item, self.db)
        self.assertEqual(registrado["nota"] * 10, registrado["pontuacao"])
        item = fila.listar(db_path=self.db)[0]
        self.assertEqual(item["nota"], registrado["nota"])
        self.assertEqual(item["origem_nota"], "HEURISTICA_PROVISORIA")

    def test_nota_humana_tem_precedencia_sem_promover_estado(self):
        primeiro = fila.registrar(self.item, self.db)["id"]
        fila.registrar({"link": "https://example.org/segunda",
                        "titulo": "Numa loja ha uma oferta nova de produtos"}, self.db)
        fila.atribuir_nota(primeiro, 10, "Prioridade para público brasileiro", self.db)
        linha = fila.listar(db_path=self.db)[0]
        self.assertEqual(linha["id"], primeiro)
        self.assertEqual(linha["nota"], 10)
        self.assertEqual(linha["estado"], "DESCOBERTA")
        self.assertEqual(linha["origem_nota"], "REVISAO_EDITORIAL")

    def test_reavaliacao_preserva_nota_humana(self):
        primeiro = fila.registrar(self.item, self.db)["id"]
        fila.atribuir_nota(primeiro, 3, "Editor optou por reduzir prioridade", self.db)
        retorno = fila.reavaliar_descobertas(db_path=self.db)
        self.assertEqual(retorno["reavaliadas"], 1)
        self.assertFalse(retorno["wordpress_alterado"])
        self.assertEqual(fila.listar(db_path=self.db)[0]["nota"], 3)

    def test_recusa_revisao_sem_rastro(self):
        uid = fila.registrar(self.item, self.db)["id"]
        with self.assertRaises(ValueError):
            fila.atribuir_nota(uid, 11, "Motivo editorial longo", self.db)
        with self.assertRaises(ValueError):
            fila.atribuir_nota(uid, 8, "breve", self.db)
        with self.assertRaises(KeyError):
            fila.atribuir_nota("inexistente", 8, "Motivo editorial longo", self.db)


if __name__ == "__main__":
    unittest.main()
