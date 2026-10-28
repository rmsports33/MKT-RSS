"""Regressões da fila RSS P0: execução offline, sem rede ou credenciais."""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0 import fila_pautas as fila


class TestFilaPautas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "pautas.db"
        self.a = {"fonte": "teste", "link": "https://example.org/android?utm_source=rss",
                  "titulo": "Google anuncia novas funções para Android em setembro",
                  "published": "2026-09-01"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_idempotencia_url_canonica(self):
        first = fila.registrar(self.a, self.db)
        second = fila.registrar({**self.a, "link": "https://example.org/android"}, self.db)
        self.assertTrue(first["novo"])
        self.assertFalse(second["novo"])
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(fila.listar(db_path=self.db)), 1)

    def test_titulo_semelhante_em_outra_fonte(self):
        first = fila.registrar(self.a, self.db)
        second = fila.registrar({**self.a, "fonte": "outro",
                                 "link": "https://another.example/report"}, self.db)
        self.assertFalse(second["novo"])
        self.assertEqual(second["motivo"], "titulo_semelhante")
        self.assertEqual(first["id"], second["id"])

    def test_estados_e_retentativa(self):
        uid = fila.registrar(self.a, self.db)["id"]
        with self.assertRaises(ValueError):
            fila.mudar_estado(uid, "CONCLUIDA", db_path=self.db)
        fila.mudar_estado(uid, "SELECIONADA", db_path=self.db)
        fila.mudar_estado(uid, "EM_PRODUCAO", db_path=self.db)
        fila.mudar_estado(uid, "SELECIONADA", motivo="falha recuperável", db_path=self.db)
        self.assertEqual(fila.listar("SELECIONADA", db_path=self.db)[0]["id"], uid)

    def test_bloqueado_nao_pode_publicar(self):
        uid = fila.registrar(self.a, self.db)["id"]
        fila.mudar_estado(uid, "BLOQUEADA", db_path=self.db)
        with self.assertRaises(ValueError):
            fila.mudar_estado(uid, "CONCLUIDA", db_path=self.db)

    def test_ranking_deterministico(self):
        a = fila.registrar(self.a, self.db)
        b = fila.registrar({"fonte": "teste", "link": "https://example.org/other",
                            "titulo": "Assunto genérico diferente"}, self.db)
        self.assertGreater(a["pontuacao"], b["pontuacao"])

    def test_falha_turso_nao_cria_sqlite_local(self):
        with patch.object(fila.cloud_db, "turso_enabled", return_value=True), \
             patch.object(fila.cloud_db, "turso_execute", return_value={"erro": "offline"}):
            with self.assertRaises(RuntimeError):
                fila.registrar(self.a)
        self.assertFalse(self.db.exists())

    def test_input_invalido(self):
        with self.assertRaises(ValueError):
            fila.registrar({**self.a, "link": "file:///etc/passwd"}, self.db)
        with self.assertRaises(ValueError):
            fila.registrar({**self.a, "titulo": ""}, self.db)


    def test_turso_simulado_preserva_entre_chamadas_independentes(self):
        """Confere o adaptador remoto com backend fake; NAO testa Turso real."""
        import sqlite3
        banco = self.db

        def fake_turso(sql, args=()):
            with sqlite3.connect(banco) as con:
                cur = con.execute(sql, args)
                if cur.description:
                    return {"rows": [list(row) for row in cur.fetchall()], "affected": 0}
                return {"rows": [], "affected": cur.rowcount}

        with patch.object(fila.cloud_db, "turso_enabled", return_value=True), \
             patch.object(fila.cloud_db, "turso_execute", side_effect=fake_turso):
            first = fila.registrar(self.a)
            self.assertTrue(first["novo"])
            # Segunda chamada com nova instância lógica, mesmo backend persistido.
            second = fila.registrar({**self.a, "link": "https://example.org/android"})
            self.assertFalse(second["novo"])
            self.assertEqual(first["id"], second["id"])
            self.assertEqual(len(fila.listar()), 1)

    def test_urls_distintas_geram_ids_distintos_sem_escrita(self):
        """A identidade por URL e a similaridade são conceitos separados."""
        left = fila._url("https://example.org/a?utm_medium=rss")
        right = fila._url("https://example.org/b")
        self.assertNotEqual(fila.hashlib.sha256(left.encode()).hexdigest()[:32],
                            fila.hashlib.sha256(right.encode()).hexdigest()[:32])

    def test_concorrencia_titulos_similares_sem_duplicacao(self):
        """Dois workers disputam o lease; apenas um grava a pauta."""
        entrou = threading.Event()
        liberar = threading.Event()
        original = fila._registrar_serializado
        outcomes = []

        def pause(*args):
            entrou.set()
            self.assertTrue(liberar.wait(timeout=5))
            return original(*args)

        def worker():
            try:
                outcomes.append(fila.registrar(self.a, self.db))
            except Exception as exc:
                outcomes.append(exc)

        with patch.object(fila, "_registrar_serializado", side_effect=pause):
            t = threading.Thread(target=worker)
            t.start()
            try:
                self.assertTrue(entrou.wait(timeout=5))
                with self.assertRaisesRegex(RuntimeError, "ocupada"):
                    fila.registrar({**self.a, "link": "https://other.example/new"}, self.db)
            finally:
                liberar.set()
                t.join(timeout=5)
        self.assertFalse(t.is_alive())
        self.assertTrue(outcomes[0]["novo"])
        duplicate = fila.registrar({**self.a, "link": "https://other.example/new"}, self.db)
        self.assertFalse(duplicate["novo"])
        self.assertEqual(len(fila.listar(db_path=self.db)), 1)

    def test_lease_liberado_apos_falha(self):
        with patch.object(fila, "_registrar_serializado", side_effect=ValueError("falha")):
            with self.assertRaises(ValueError):
                fila.registrar(self.a, self.db)
        self.assertTrue(fila.registrar(self.a, self.db)["novo"])

if __name__ == "__main__":
    unittest.main()
