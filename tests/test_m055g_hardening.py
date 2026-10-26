"""M05.5-G regression checks (offline, no external provider)."""
import math
import pytest
from mkt_flow_p0.editorial_pilot import Policy, evaluate
from mkt_flow_p0.editorial_negative_checks import check_preview, check_rendered

SOURCE = "Wi-Fi 7 anunciado com canais de 320 MHz."
def forbidden(_):
    raise AssertionError("callback must not execute")

@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf"), -1.0, 0.0])
def test_invalid_money_blocks_before_callback(invalid):
    for slot in ("max_cost_usd", "input_usd_per_1k", "output_usd_per_1k"):
        kwargs = {"approved": True, "model": "offline-test", "max_cost_usd": 1.,
                  "input_usd_per_1k": .001, "output_usd_per_1k": .002}
        kwargs[slot] = invalid
        r = evaluate(SOURCE, Policy(**kwargs), forbidden)
        assert r["motivo"] == "limites_invalidos" and not r["escreveu"]

def test_mismatched_price_date_is_blocked():
    evidence = "Produto A custa R$ 100 em 2026-10-01. Produto B custa R$ 200 em 2026-10-02."
    claim = "Produto A custa R$ 100 em 2026-10-02."
    # same price/date appear separately, but never paired in the source
    r = check_preview(evidence, {"texto_markdown": claim})
    assert r["veredito"] == "BLOQUEADO"

def test_html_is_checked_after_render():
    r = check_rendered(SOURCE, "<p>Testamos em nossa bancada e obtivemos 9999 Mbps</p>",
                       {"titulo_seo": "Wi-Fi 7"})
    assert r["veredito"] == "BLOQUEADO"
    assert any("texto_markdown" in x for x in r["motivos"])

def test_missing_html_blocks():
    assert check_rendered(SOURCE, "", {})["veredito"] == "BLOQUEADO"

def test_clean_html_never_certified():
    r = check_rendered(SOURCE, "<p>Wi-Fi 7 com canais de 320 MHz.</p>", {})
    assert r["veredito"] == "REVISAO_OBRIGATORIA" and r["certificacao_factual"] is False
