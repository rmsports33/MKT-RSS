"""Modo --queue-only: integração opt-in, sem rede, LLM ou WordPress."""
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pipeline_rss


class TestPipelineQueueOnly(unittest.TestCase):
    def test_collect_somente_com_flag(self):
        expected = {"novas": 2, "duplicadas": 1, "falhas": []}
        with patch.object(sys, "argv", ["pipeline_rss.py", "--queue-only", "--fonte", "9to5google", "--limit", "3"]), \
             patch("rss_queue_collect.coletar", return_value=expected) as coletar:
            output = io.StringIO()
            with redirect_stdout(output):
                pipeline_rss.main()
        coletar.assert_called_once_with(fonte="9to5google", limite=3)
        self.assertEqual(json.loads(output.getvalue()), expected)

    def test_falha_retorna_erro_sem_wp(self):
        with patch.object(sys, "argv", ["pipeline_rss.py", "--queue-only"]), \
             patch("rss_queue_collect.coletar", return_value={"novas": 0, "duplicadas": 0, "falhas": [{"fonte": "feed", "motivo": "offline"}]}):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                pipeline_rss.main()
        self.assertEqual(ctx.exception.code, 1)

    def test_modo_fila_nao_aceita_dry_run(self):
        with patch.object(sys, "argv", ["pipeline_rss.py", "--queue-only", "--dry-run"]):
            with self.assertRaises(SystemExit) as ctx:
                pipeline_rss.main()
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
