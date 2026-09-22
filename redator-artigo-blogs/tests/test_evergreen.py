"""
Testes da cadeia evergreen (OpenRouter -> Groq -> Ollama), tudo mockado.
pytest redator-artigo-blogs/tests/test_evergreen.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
import src.evergreen as E


def _resp(texto="corpo"):
    m = MagicMock()
    m.choices = [MagicMock(message=MagicMock(content=texto))]
    return m


def test_openrouter_primeiro(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("GROQ_API_KEY", "g")
    with patch.object(E, "_try_call", return_value=_resp()) as mc:
        r = E.gerar_texto("s", "u")
        assert r["provedor"] == "openrouter" and mc.call_count == 1


def test_groq_fallback(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("GROQ_API_KEY", "g")
    with patch.object(E, "_try_call", side_effect=[Exception("429"), _resp()]):
        r = E.gerar_texto("s", "u")
        assert r["provedor"] == "groq" and "openrouter" in r["avisos"][0]


def test_ollama_ultimo_e_erro(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch.object(E, "_try_call", return_value=_resp()):
        assert E.gerar_texto("s", "u")["provedor"] == "ollama"
    with patch.object(E, "_try_call", side_effect=Exception("down")):
        assert "erro" in E.gerar_texto("s", "u")


def test_try_call_tem_timeout_explicito(monkeypatch):
    import sys
    import types
    chamadas = {}

    class FakeCompletions:
        def create(self, **kw):
            chamadas.update(kw)
            return _resp()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kw):
            pass
        chat = FakeChat()

    mod = types.ModuleType("openai")
    mod.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", mod)
    E._try_call("k", "https://x", "m", 0.5, "s", "u")
    assert chamadas.get("timeout") == E.LLM_TIMEOUT_S
