"""
Testes legados — MKTFLOW.ml_client (urlopen/sleep mockados)
pytest tests/test_ml_client.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import io
import json
sys.path.insert(0, str(Path(__file__).parent.parent / "MKTFLOW"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from MKTFLOW.ml_client import consultar_api_publica_mercado_livre as consultar, extrair_item_id


def _fake_urlopen(payload):
    m = MagicMock()
    m.read.return_value = json.dumps(payload).encode()
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


def test_extrair_item_id():
    assert extrair_item_id("https://x/MLB123?matt_word=a") == "MLB123"


def test_sucesso_e_cache():
    payload = {"title": "P", "price": 20.0, "available_quantity": 2, "status": "active"}
    with patch("MKTFLOW.ml_client.urllib.request.urlopen", return_value=_fake_urlopen(payload)) as uo:
        r1 = consultar("MLB111111111")
        r2 = consultar("MLB111111111")
        assert r1["titulo"] == "P" and r2["origem"] == "cache" and uo.call_count == 1


def test_retry_apos_erro():
    import urllib.error
    payload = {"title": "P", "price": 1.0, "available_quantity": 1, "status": "active"}
    def fake_urlopen(req, timeout=None):
        if not hasattr(fake_urlopen, "n"):
            fake_urlopen.n = 0
        fake_urlopen.n += 1
        if fake_urlopen.n == 1:
            raise urllib.error.HTTPError(req.full_url, 500, "x", {}, io.BytesIO(b""))
        return _fake_urlopen(payload)
    with patch("MKTFLOW.ml_client.urllib.request.urlopen", side_effect=fake_urlopen):
        with patch("MKTFLOW.ml_client.time.sleep") as ms:
            r = consultar("MLB222222222")
            assert r["titulo"] == "P" and ms.called


def test_404():
    import urllib.error
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "x", {}, io.BytesIO(b""))
    with patch("MKTFLOW.ml_client.urllib.request.urlopen", side_effect=fake_urlopen):
        assert "erro" in consultar("MLB333333333")


def test_timeout():
    with patch("MKTFLOW.ml_client.urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        assert "expirou" in consultar("MLB444444444")["erro"]


def test_preco_vazio_sem_cache():
    import MKTFLOW.ml_client as M
    payload = {"title": "", "price": None, "available_quantity": 0, "status": "active"}
    def fake_empty_price(req, timeout=None):
        return _fake_urlopen(payload)
    with patch("MKTFLOW.ml_client.urllib.request.urlopen", side_effect=fake_empty_price):
        consultar("MLB555555555")
        assert "MLB555555555" not in M._CACHE
