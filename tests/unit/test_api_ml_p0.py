"""
Testes P0 — api_ml (cache TTL, 404/timeout não cacheiam)
pytest tests/test_api_ml_p0.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
import mkt_flow_p0.api_ml as M


def _resp(payload, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = payload
    m.raise_for_status.side_effect = None if status < 400 else Exception("http")
    return m


def test_id_invalido():
    assert "erro" in M.consultar_api_publica_mercado_livre("XXX")


def test_id_vazio():
    assert "erro" in M.consultar_api_publica_mercado_livre("")


def test_cache_hit():
    M._limpar_cache()
    payload = {"title": "Fone", "price": 199.9, "available_quantity": 5, "status": "active"}
    with patch.object(M._session, "get", return_value=_resp(payload)) as g:
        r1 = M.consultar_api_publica_mercado_livre("MLB123456789")
        r2 = M.consultar_api_publica_mercado_livre("MLB123456789")
        assert r1["origem"] == "api" and r2["origem"] == "cache"
        assert g.call_count == 1
        assert r1["titulo"] == "Fone"


def test_404_nao_cacheia():
    M._limpar_cache()
    m = MagicMock()
    m.status_code = 404
    with patch.object(M._session, "get", return_value=m):
        assert "erro" in M.consultar_api_publica_mercado_livre("MLB000000001")
        assert "MLB000000001" not in M._CACHE


def test_timeout():
    import requests
    with patch.object(M._session, "get", side_effect=requests.Timeout("t")):
        r = M.consultar_api_publica_mercado_livre("MLB123456789", usar_cache=False)
        assert "expirou" in r["erro"]


def test_erro_nao_cacheia():
    M._limpar_cache()
    with patch.object(M._session, "get", side_effect=Exception("rede")):
        M.consultar_api_publica_mercado_livre("MLB999999999", usar_cache=False)
        assert "MLB999999999" not in M._CACHE
