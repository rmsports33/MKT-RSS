"""Real comparative generator must receive editorial direction before LLM call."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "redator-artigo-blogs"))
from src.generator.render import gerar_comparativo


def test_editorial_brief_is_injected_into_actual_llm_prompt():
    brief = {
        "genre": "comparativo",
        "reader": "Leitor que precisa escolher entre dois celulares para tarefas cotidianas.",
        "need": "Distinguir limitações reais de cada aparelho sem depender de marketing.",
        "angle": "Explicar quais diferenças verificadas importam para cada perfil de uso.",
        "contribution": "Fornecer critérios concretos de escolha com base apenas nas fichas.",
        "limits": "Não alegar testes próprios, preços atuais ou especificações não fornecidas.",
    }
    captured = {}

    def llm(system, payload):
        captured["system"] = system
        captured["payload"] = payload
        return "## Escolha\nA ficha disponível não comprova desempenho em testes reais."

    result = gerar_comparativo(
        [{"nome": "Modelo A", "specs": {}, "fonte": "Fabricante A"},
         {"nome": "Modelo B", "specs": {}, "fonte": "Fabricante B"}],
        chamar_llm=llm, editorial_brief=brief)
    assert "erro" not in result
    assert "BRIEFING EDITORIAL" in captured["system"]
    assert brief["angle"] in captured["system"]
    assert "Voz independente" in captured["system"]


def test_invalid_brief_fails_before_llm_call():
    called = []
    with pytest.raises(ValueError, match="briefing editorial"):
        gerar_comparativo([], chamar_llm=lambda *args: called.append(args),
                         editorial_brief={"genre": "comparativo"})
    assert not called
