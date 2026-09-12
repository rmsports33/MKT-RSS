"""
Testes P0 — rss_ingestor (offline: XML real + session mockada)
pytest tests/test_rss_ingestor_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.rss_ingestor as R

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Tech</title>
<item><title>Fone JBL em oferta</title><link>https://exemplo.com/fone</link><pubDate>Mon, 01 Sep 2026 10:00:00 GMT</pubDate><description>Resumo</description></item>
<item><title>Mouse gamer review</title><link>https://exemplo.com/mouse</link><pubDate>Mon, 01 Sep 2026 11:00:00 GMT</pubDate><description>Resumo 2</description></item>
</channel></rss>"""


def _resp_ok():
    m = MagicMock()
    m.content = RSS_XML.encode()
    m.raise_for_status.return_value = None
    return m


def test_fetch_feed_offline():
    with patch.object(R._session, "get", return_value=_resp_ok()):
        r = R.fetch_feed("https://exemplo.com/feed", fonte="exemplo", max_items=5)
        assert r["total"] == 2 and r["itens"][0]["titulo"] == "Fone JBL em oferta"


def test_dedup_url_e_similaridade(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DB_PATH", tmp_path / "rss.db")
    assert R.item_ja_visto("https://e.com/a", "Fone JBL em oferta") is False
    R.marcar_visto("ex", "https://e.com/a", "Fone JBL em oferta")
    assert R.item_ja_visto("https://e.com/a", "Outro título") is True
    assert R.item_ja_visto("https://e.com/b", "Fone JBL em OFERTA!!") is True


def test_buscar_novidades_filtra(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "DB_PATH", tmp_path / "rss2.db")
    with patch.object(R._session, "get", return_value=_resp_ok()):
        r1 = R.buscar_novidades("https://exemplo.com/feed", fonte="ex", limit=5)
        r2 = R.buscar_novidades("https://exemplo.com/feed", fonte="ex", limit=5)
        assert r1["total_novos"] == 2 and r2["total_novos"] == 0


def test_feed_erro():
    with patch.object(R._session, "get", side_effect=Exception("rede")):
        assert "erro" in R.fetch_feed("https://exemplo.com/feed")
