"""
Testes P0 — extractor (offline: HTML estático via session mockada)
pytest tests/test_extractor_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.extractor import extrair_conteudo, contar_palavras, _texto_documento

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


def test_document_mode_keeps_price_cards_and_legal_headings():
    html = ('<html><head><script>FAKE_PRICE $999</script></head><body>'
            '<nav>MENU</nav><section><h2>Privacy Choices</h2>'
            '<h3>$499/mo Subscription</h3><h3>$20,000 Ownership</h3>'
            '<p><strong>Payment</strong> information</p></section>'
            '<p hidden>HIDDEN PRICE</p><p style="display: none">HIDDEN OFFER</p>'
            '<footer>FOOTER</footer></body></html>')
    text = _texto_documento(html)
    assert all(value in text for value in ['Privacy Choices', '$499/mo', '$20,000', 'Payment information'])
    assert all(value not in text for value in ['FAKE_PRICE', 'HIDDEN', 'MENU', 'FOOTER'])


def test_full_document_extraction_is_opt_in():
    response = _resp_html()
    response.text = HTML.replace('<article>', '<h2>Privacy Choices</h2><article>')
    with patch('mkt_flow_p0.extractor._session.get', return_value=response):
        result = extrair_conteudo('https://example.org/legal', preservar_documento=True)
    assert result['origem'] == 'html_documento'
    assert 'Privacy Choices' in result['texto'] and result['qualidade_ok']


def test_rendered_capture_keeps_real_page_text_and_provenance():
    body = 'Texto capturado no navegador. ' * 110 + '$499 $20,000 $200'
    with patch('mkt_flow_p0.extractor._documento_renderizado', return_value={
            'texto': body, 'titulo': 'Order NEO', 'final_url': 'https://www.1x.tech/order'}):
        result = extrair_conteudo('https://www.1x.tech/order', renderizar=True)
    assert result['texto'] == body
    assert result['origem'] == 'playwright_documento'
    assert result['qualidade_ok']


def test_failed_rendering_does_not_synthesize_a_source():
    with patch('mkt_flow_p0.extractor._documento_renderizado', side_effect=RuntimeError('private detail')):
        result = extrair_conteudo('https://www.1x.tech/order', renderizar=True)
    assert 'erro' in result and 'private detail' not in result['erro']
    assert 'texto' not in result
