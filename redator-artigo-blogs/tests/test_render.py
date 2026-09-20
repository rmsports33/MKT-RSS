"""
Testes do redator (LLM sempre injetado/mockado — zero custo)
pytest redator-artigo-blogs/tests -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.generator.render import (
    _sanitizar_llm_html, _remover_alusao_teste, _detectar_hallucination,
    montar_tabela_specs, montar_pagina, gerar_comparativo,
)
from src.generator.prompt import montar_system_prompt


def _modelos():
    return [
        {"nome": "Fone A", "specs": {"bateria.mah": "5000", "peso.g": "200"}, "fonte": "fab A"},
        {"nome": "Fone B", "specs": {"bateria.mah": "4000", "peso.g": "180"}, "fonte": "fab B"},
    ]


def test_prompt_tem_regras():
    s = montar_system_prompt("celular")
    assert "não informado" in s and "bancada" in s


def test_prompt_nao_manda_placeholder_em_texto():
    s = montar_system_prompt("celular")
    assert "NUNCA escreva '— não informado'" in s and "inches" in s


def test_sanitiza_e_filtra_fonte():
    h = _sanitizar_llm_html("## T\nTexto **forte** [fonte: fab A] [fonte: blog X]", ["fab A"])
    assert "<h2>" in h and "<strong>forte</strong>" in h
    assert "[fonte: fab A]" not in h and "blog X" not in h
    assert '<sup class="fonte-ref">[1]</sup>' in h and "fonte-list" in h


def test_fonte_nao_permitida_sai_por_completo():
    h = _sanitizar_llm_html("Texto [fonte: blog X]", ["fab A"])
    assert "fonte-list" not in h and "blog X" not in h and "fab A" not in h


def test_placeholder_marcador_eh_removido():
    h = _sanitizar_llm_html("## T\n[TABELA INSERIDA]\nTexto real [FOTO: galeria] aqui.")
    assert "[TABELA INSERIDA]" not in h and "[FOTO: galeria]" not in h
    assert "Texto real" in h and "aqui" in h and "<p>[]</p>" not in h


def test_tabela_hr_e_h2():
    h = _sanitizar_llm_html("## T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n—\n\nTexto")
    assert h.count("<table") == 1 and "<th>a</th>" in h and "<td>1</td>" in h
    assert "<hr>" in h and "<p>---</p>" not in h and "<p>—</p>" not in h


def test_remove_bancada():
    t = _remover_alusao_teste("Testamos em bancada e gostamos. Boa bateria.")
    assert "bancada" not in t.lower() and "Boa bateria" in t


def test_detecta_numero_fora_das_specs():
    specs = {"bateria.mah": "5000"}
    sus = _detectar_hallucination("Bateria 5000 mAh e tela de 120 Hz.", specs)
    assert any("120" in s for s in sus) and not any("5000" in s for s in sus)


def test_detecta_token_spec_fora():
    specs = {"gpu": "Adreno 610", "armazenamento.tipo": "UFS 2.2"}
    sus = _detectar_hallucination("GPU Adreno 618 com UFS 3.0 e Snapdragon 685.", specs)
    assert any("Adreno 618" in s for s in sus)
    assert any("UFS 3.0" in s for s in sus)
    assert any("685" in s for s in sus)  # 685 também não está neste dict
    sus2 = _detectar_hallucination("GPU Adreno 610 com UFS 2.2.", specs)
    assert sus2 == []


def test_tabela_e_pagina():
    tab = montar_tabela_specs(_modelos())
    assert "Bateria (mAh)" in tab and "bateria.mah" not in tab
    assert "5000" in tab and "compare-table" in tab
    pag = montar_pagina("Fone A vs Fone B — Comparativo", "desc", _modelos(), "audio", "<p>corpo</p>")
    assert '"@type": "Article"' in pag and "adsense-top" in pag and "<h1>" in pag


def test_tabela_rotulo_desconhecido_fica_cru():
    tab = montar_tabela_specs([{"nome": "X", "specs": {"chave_nova": "1"}}])
    assert "chave_nova" in tab


def test_tabela_sem_valor_sai_em_dash():
    tab = montar_tabela_specs([
        {"nome": "A", "specs": {"peso.g": "200"}},
        {"nome": "B", "specs": {}},
    ])
    assert "200" in tab and "—" in tab and "não informado" not in tab


def test_grafico_escondido_sem_preco():
    pag = montar_pagina("A vs B", "d", _modelos(), "audio", "<p>x</p>")
    assert "price-history" not in pag


def test_grafico_com_preco_tem_fallback():
    hist = {"Fone A": [{"data": "2026-09-01", "preco": 1500.5}]}
    pag = montar_pagina("A vs B", "d", _modelos(), "audio", "<p>x</p>", price_history=hist)
    assert "price-history" in pag and "price-fallback" in pag and "1.500,50" in pag
    assert "R$ 1500.5" not in pag


def test_preco_formatado_ptbr_e_sem_none():
    hist = {
        "Fone A": [
            {"data": "2026-09-01", "preco": 1500.5},
            {"data": "2026-09-02", "preco": 3000},
        ],
        "Fone B": [{"data": "2026-09-01", "preco": None}],
    }
    pag = montar_pagina("A vs B", "d", _modelos(), "audio", "<p>x</p>", price_history=hist)
    assert "1.500,50" in pag and "3.000,00" in pag
    assert "R$ None" not in pag


def test_preco_string_ptbr_normalizada():
    hist = {"Fone A": [{"data": "2026-09-01", "preco": "1.600,00"}]}
    pag = montar_pagina("A vs B", "d", _modelos(), "audio", "<p>x</p>", price_history=hist)
    assert "1.600,00" in pag


def test_grafico_preco_nulo_nao_gera_secao():
    hist = {"Fone A": [{"data": "2026-09-01", "preco": None}]}
    pag = montar_pagina("A vs B", "d", _modelos(), "audio", "<p>x</p>", price_history=hist)
    assert "price-history" not in pag


def test_titulo_usa_marca():
    pag = montar_pagina("Fone A vs Fone B — Comparativo", "desc", _modelos(), "audio", "<p>corpo</p>")
    assert "| ConexoTech" in pag and "| Redator" not in pag
    assert "Redação ConexoTech" in pag


def test_gerar_comparativo_injetado():
    def fake_llm(system, payload):
        assert "specs_PASS" in payload
        return "## TL;DR\nFone A tem bateria maior. [fonte: fab A]"
    r = gerar_comparativo(_modelos(), "audio", chamar_llm=fake_llm)
    assert "Fone A vs Fone B" in r["titulo"] and r["provedor"] == "injetado"
    assert r["auditoria"]["fontes"] == ["fab A", "fab B"]


def test_sem_specs_vira_nao_informado():
    tab = montar_tabela_specs([{"nome": "X", "specs": {}}])
    assert tab == ""
