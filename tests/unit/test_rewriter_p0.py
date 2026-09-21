"""
Testes P0 — rewriter (mockado, sem custo de API)
pytest tests/test_rewriter_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.rewriter import (
    gerar_slug,
    adicionar_atribuicao,
    reescrever_materia,
    _parse_json_resposta,
)


def test_slug():
    assert gerar_slug("Melhor Headphone em 2026: 10 Modelos!") == "melhor-headphone-em-2026-10-modelos"
    assert gerar_slug("") == "materia"


def test_parse_json_com_cerca():
    raw = '```json\n{"titulo_seo":"T","meta_description":"M","slug":"s","tags":[],"texto_markdown":"x"}\n```'
    d = _parse_json_resposta(raw)
    assert d["slug"] == "s"


def test_gate_texto_curto():
    r = reescrever_materia("T", "poucas palavras aqui", fonte_nome="X")
    assert "erro" in r and "curto" in r["erro"].lower()


def test_rewrite_mockado(monkeypatch):
    import mkt_flow_p0.rewriter as R

    corpo = "palavra " * 150
    fake_json = (
        '{"titulo_seo":"Titulo SEO de teste com palavra chave",'
        ' "meta_description":"' + "d" * 150 + '",'
        ' "slug":"titulo-seo-teste","tags":["tech","teste"],'
        ' "texto_markdown":"' + ("conteudo reescrito " * 120) + '"}'
    )

    class FakeMsg:
        content = fake_json

    class FakeChoice:
        message = FakeMsg()

    class FakeResp:
        choices = [FakeChoice()]
        usage = type("U", (), {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300})()

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["model"]
            return FakeResp()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(R, "_get_client", lambda: (FakeClient(), ""))
    r = reescrever_materia("Original", corpo, fonte_nome="Adrenaline", url_fonte="https://x")
    assert r["slug"] == "titulo-seo-teste"
    assert r["palavras"] >= 200
    assert r["uso_tokens"]["total"] == 300
    assert r["custo_usd_estimado"] >= 0


def test_prompt_ptbr_e_keywords():
    from mkt_flow_p0.rewriter import montar_prompt
    p = montar_prompt("Apple launches X", "Some english body text here.", "9to5Mac",
                      keywords=["apple x preço", "apple x vale a pena"])
    assert "português brasileiro" in p
    assert "apple x preço" in p
    p2 = montar_prompt("T", "corpo", "Blog")
    assert "Palavras-chave" not in p2


def test_atribuicao():
    t = adicionar_atribuicao("texto", "Adrenaline", "https://adrenaline.com.br/x")
    assert "Fonte original" in t and "adrenaline.com.br/x" in t
    assert adicionar_atribuicao("texto", "", "") == "texto"
