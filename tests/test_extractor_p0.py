"""
Testes P0 — extractor (offline: HTML estático via session mockada)
pytest tests/test_extractor_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.extractor import extrair_conteudo, contar_palavras

PARAGRAFOS = "\n".join(
    f"<p>Parágrafo {i}: análise técnica do fone XPTO cobrindo graves (tema {i}), médios, agudos, "
    f"palco sonoro, bateria de {20+i} horas, Bluetooth 5.{i%4}, cancelamento de ruído nível {i%5} "
    f"e conforto para uso prolongado no trabalho remoto e viagens longas de avião.</p>"
    for i in range(1, 31)
)
HTML = ("<html><head><title>Review Fone XPTO</title>"
        '<meta name="author" content="Redação"><meta property="og:image" content="https://e.com/img.jpg">'
        "</head><body><nav>menu</nav><article><h1>Review Fone XPTO</h1>"
        + PARAGRAFOS +
        "</article><footer>rodapé</footer></body></html>")


def _resp_html():
    m = MagicMock()
    m.text = HTML
    m.raise_for_status.return_value = None
    return m


def test_extracao_offline_ok():
    with patch("mkt_flow_p0.extractor._session.get", return_value=_resp_html()):
        r = extrair_conteudo("https://exemplo.com/review")
        assert r["qualidade_ok"] is True and r["palavras"] >= 400
        assert "menu" not in (r["texto"] or "") and "Parágrafo 7" in r["texto"]


def test_url_invalida():
    assert "erro" in extrair_conteudo("nota-url")


def test_contar_palavras():
    assert contar_palavras("a b  c") == 3 and contar_palavras("") == 0
