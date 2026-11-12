import hashlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mkt_flow_p0 import rewriter


TEST_EDITORIAL_BRIEF = {
    "genre": "noticia",
    "reader": "Leitores que precisam interpretar documentação técnica disponível.",
    "need": "Identificar consequências e limites dos fatos fornecidos nas fontes.",
    "angle": "Distinguir informação documentada de hipótese ainda não demonstrada.",
    "contribution": "Explicar critérios práticos sustentados pelos documentos fornecidos.",
    "limits": "Não inventar testes próprios, preços, medições ou experiências de uso."
}


class GroqTraceFingerprintTests(unittest.TestCase):
    def test_exact_prompt_messages_are_fingerprinted(self):
        observed = {}
        article = " ".join(["conteudo"] * 220)
        payload = {
            "titulo_seo": "Titulo de teste sobre IA",
            "meta_description": "Descrição do teste com conteúdo útil e informativo. " * 3,
            "slug": "teste-ia",
            "tags": ["inteligencia artificial"],
            "texto_markdown": article,
        }

        def create(**kwargs):
            observed["messages"] = kwargs["messages"]
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(payload))
                )],
                usage=SimpleNamespace(prompt_tokens=23, completion_tokens=42),
            )

        mock_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        with patch.object(rewriter, "_get_client", return_value=(mock_client, "")):
            result = rewriter.reescrever_materia(
                "Pauta sobre inteligência artificial",
                " ".join(["texto"] * 110),
                editorial_brief=TEST_EDITORIAL_BRIEF,
            )
        self.assertNotIn("erro", result)
        expected = hashlib.sha256(json.dumps(
            observed["messages"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        self.assertEqual(result["prompt_sha256"], expected)
        self.assertEqual(observed["messages"][0]["role"], "system")
        self.assertEqual(observed["messages"][1]["role"], "user")
        self.assertNotIn(article, observed["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
