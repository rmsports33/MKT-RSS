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
    assert result["referencias_traducao"] == {sentence.casefold(): ["c1"]}
    assert "contrato_editorial" in result


def test_rewriter_invalid_references_are_not_passed(monkeypatch):
    payload = {
        "texto_markdown": " ".join(["Texto válido."] * 210),
        "referencias_traducao": {"texto válido.": ["c1", 2], "": ["c1"]},
    }
    monkeypatch.setattr(rewriter, "_get_client", lambda: (fake_client(payload), ""))
    result = rewriter.reescrever_materia("Teste", " ".join(["origem"] * 110))
    assert result["referencias_traducao"] == {}
