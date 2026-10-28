"""Checagem do bloqueio obrigatório antes de conectar ao Turso."""
import os
import unittest
from unittest.mock import patch
from scripts.rss_queue_turso_homolog_probe import guard


class TestTursoHomologGuard(unittest.TestCase):
    def test_sem_token_bloqueado(self):
        with patch.dict(os.environ, {"TURSO_DATABASE_URL": "libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io", "TURSO_AUTH_TOKEN": ""}):
            with self.assertRaises(RuntimeError):
                guard()

    def test_banco_producao_bloqueado(self):
        with patch.dict(os.environ, {"TURSO_DATABASE_URL": "libsql://mkt-rss-rmsports33.aws-ap-northeast-1.turso.io", "TURSO_AUTH_TOKEN": "fake"}):
            with self.assertRaises(RuntimeError):
                guard()

    def test_homolog_aceito_sem_abrir_conexao(self):
        with patch.dict(os.environ, {"TURSO_DATABASE_URL": "libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io", "TURSO_AUTH_TOKEN": "fake"}):
            guard()
