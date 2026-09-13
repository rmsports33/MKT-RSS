"""
Testes P0 — format (offline)
pytest tests/test_format_p0.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.format import markdown_para_html, truncar_palavras, sanitizar_url


def test_negrito_e_link():
    h = markdown_para_html("Isto é **forte** e [fonte](https://x.com/a)")
    assert "<strong>forte</strong>" in h and '<a href="https://x.com/a"' in h
    assert "**" not in h


def test_headings_listas_hr():
    md = "## Título\n\n1. Um\n2. Dois\n\n- A\n- B\n\n---\n\nTexto"
    h = markdown_para_html(md)
    assert "<h2>Título</h2>" in h and "<ol>" in h and "<ul>" in h and "<hr>" in h


def test_xss_escapado_antes_do_bold():
    h = markdown_para_html('<script>alert(1)</script> **ok**')
    assert "<script>" not in h and "<strong>ok</strong>" in h


def test_truncar_fronteira():
    assert truncar_palavras("Fabricantes opinam sobre isso", 20) == "Fabricantes opinam"
    assert truncar_palavras("Curto", 60) == "Curto"
    assert "opi" not in truncar_palavras("Fabricantes opinam", 16).split()[-1:]


def test_sanitizar_url():
    assert sanitizar_url("https://x.com/vaza-odispositivo/") == "https://x.com/vaza-odispositivo/"
    assert "­" not in sanitizar_url("https://x.com/vaza-o­dispositivo/")
    assert sanitizar_url("https://x.com/a" + chr(0) + "b ") == "https://x.com/ab"
