"""Exercise the actual JSON rewriter adapter without provider requests."""
import json
from types import SimpleNamespace
from mkt_flow_p0 import rewriter


def fake_client(payload):
    message = SimpleNamespace(content=json.dumps(payload))
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=None)
    completions = SimpleNamespace(create=lambda **kwargs: response)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_rewriter_preserves_optional_references_without_any_network(monkeypatch):
    sentence = "O produto teve uma atualização."
    payload = {
        "titulo_seo": "Teste", "meta_description": "Descrição",
        "slug": "teste", "tags": ["tecnologia"],
        "texto_markdown": " ".join([sentence] * 210),
        "referencias_traducao": {sentence.casefold(): ["c1"]},
    }
    monkeypatch.setattr(rewriter, "_get_client", lambda: (fake_client(payload), ""))
    result = rewriter.reescrever_materia("Teste", " ".join(["original"] * 110))
    assert "erro" not in result
    assert result["referencias_traducao"] == {}  # without approved claim IDs, all references are rejected
    assert "contrato_editorial" in result


def test_rewriter_invalid_references_are_not_passed(monkeypatch):
    payload = {
        "texto_markdown": " ".join(["Texto válido."] * 210),
        "referencias_traducao": {"texto válido.": ["c1", 2], "": ["c1"]},
    }
    monkeypatch.setattr(rewriter, "_get_client", lambda: (fake_client(payload), ""))
    result = rewriter.reescrever_materia("Teste", " ".join(["origem"] * 110))
    assert result["referencias_traducao"] == {}

def test_only_supplied_claim_ids_reach_output_and_prompt(monkeypatch):
    contract = {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "url": "https://example.org/source", "status": "PASS",
                     "retrieved_at": "2026-10-26"}],
        "claims": [{"id": "c1", "text": "Original claim.", "status": "PASS",
                    "evidence_ids": ["s1"]}],
    }
    seen = {}
    def capture_client(payload):
        client = fake_client(payload)
        original_create = client.chat.completions.create
        def invoke(**kwargs):
            seen["prompt"] = kwargs["messages"][1]["content"]
            return original_create(**kwargs)
        client.chat.completions.create = invoke
        return client
    output = {"texto_markdown": " ".join(["Texto traduzido."] * 210),
              "referencias_traducao": {"texto traduzido.": ["c1"],
                                      "alegação inventada.": ["fake"]}}
    monkeypatch.setattr(rewriter, "_get_client", lambda: (capture_client(output), ""))
    result = rewriter.reescrever_materia("Teste", " ".join(["origem"] * 110),
                                         evidencias_aprovadas=contract)
    assert result["referencias_traducao"] == {"texto traduzido.": ["c1"]}
    assert '"id": "c1"' in seen["prompt"]
    assert "Original claim." in seen["prompt"]
    assert '"id": "fake"' not in seen["prompt"]
    assert result["contrato_editorial"] is None  # translated text is not literal certification


def test_invalid_contract_fails_before_provider(monkeypatch):
    monkeypatch.setattr(rewriter, "_get_client",
                        lambda: (_ for _ in ()).throw(AssertionError("provider invoked")))
    result = rewriter.reescrever_materia(
        "Teste", " ".join(["origem"] * 110),
        evidencias_aprovadas={"claims": [{"id": "fake", "status": "PASS"}]})
    assert "erro" in result
