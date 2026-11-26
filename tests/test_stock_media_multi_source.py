"""Testes das duas fontes de fotos gratuitas. Sem rede real."""
import json
import time

import pytest

from mkt_flow_p0 import stock_media_multi_source as sm

HIT_PIXABAY = {
    "largeImageURL": "https://pixabay.com/get/ed6a99fd0a76647_1280.jpg",
    "pageURL": "https://pixabay.com/photos/teste-123/",
    "user": "AutorPixabay", "imageWidth": 1920, "imageHeight": 1080,
}
HIT_UNSPLASH = {
    "urls": {"regular": "https://images.unsplash.com/photo-123"},
    "links": {"html": "https://unsplash.com/photos/abc"},
    "user": {"name": "Autor"}, "width": 1600, "height": 900,
}


class _Resp:
    def __init__(self, body):
        self._body = body
    def raise_for_status(self):
        return None
    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
    def get(self, url, **kw):
        self.calls.append({"url": url, "params": kw.get("params") or {},
                           "headers": kw.get("headers") or {}})
        if "unsplash" in url:
            return _Resp(self.responses.get("unsplash", {"results": []}))
        if "pixabay" in url:
            return _Resp(self.responses.get("pixabay", {"hits": []}))
        return _Resp({})


def test_unsplash_candidato_valido(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    s = _Session({"unsplash": {"results": [HIT_UNSPLASH]}})
    out = sm.buscar_unsplash("tecnologia", session=s, usar_cache=False)
    assert len(out["candidatos"]) == 1
    c = out["candidatos"][0]
    assert c["origem"] == "unsplash"
    assert c["revisao_direitos"] == "PENDENTE"
    assert c["credito_exibicao"] == "Foto: Autor / Unsplash"


def test_pixabay_candidato_valido_url_real(monkeypatch):
    """largeImageURL real da API vem de pixabay.com/get/, não de cdn."""
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [HIT_PIXABAY]}})
    out = sm.buscar_pixabay("tecnologia", session=s, usar_cache=False)
    assert len(out["candidatos"]) == 1
    c = out["candidatos"][0]
    assert c["origem"] == "pixabay"
    assert c["download_para_servidor"] is True
    assert c["credito_exibicao"] == "Foto: AutorPixabay / Pixabay"


def test_pixabay_envia_lang_pt_e_nao_codifica_q(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": []}})
    sm.buscar_pixabay("smartphone 5g", session=s, usar_cache=False)
    params = s.calls[0]["params"]
    assert params["lang"] == "pt"
    assert params["q"] == "smartphone 5g"
    assert params["key"] == "chave-teste"
    assert len(params["q"]) <= sm.MAX_Q_CHARS


def test_q_limitado_a_100_caracteres(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": []}})
    sm.buscar_pixabay("a" * 250, session=s, usar_cache=False)
    assert len(s.calls[0]["params"]["q"]) == 100


def test_pixabay_http_rejeitado(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [dict(HIT_PIXABAY,
                    largeImageURL="http://pixabay.com/get/x.jpg")]}})
    out = sm.buscar_pixabay("x", session=s, usar_cache=False)
    assert out["candidatos"] == []


def test_fallback_para_pixabay_quando_unsplash_vazio(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [HIT_PIXABAY]}})
    out = sm.buscar_candidatos("tecnologia", session=s, usar_cache=False)
    assert out["ultima_fonte"] == "pixabay"
    assert any(c["origem"] == "pixabay" for c in out["candidatos"])
    assert out["revisao_direitos"] == "PENDENTE"


def test_sem_chave_pixabay_falha_segura(monkeypatch):
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    out = sm.buscar_pixabay("x", session=_Session({}), usar_cache=False)
    assert out.get("erro") == "PIXABAY_KEY_AUSENTE"


def test_url_licenca_pixabay_oficial():
    """URL conferida em pixabay.com/service/license-summary/ (26/11/2026)."""
    assert sm.PIXABAY_LICENSE == "https://pixabay.com/service/license-summary/"


def test_cache_24h_evita_segunda_chamada(monkeypatch, tmp_path):
    monkeypatch.setenv("STOCK_MEDIA_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [HIT_PIXABAY]}})
    r1 = sm.buscar_pixabay("tema cache", session=s, usar_cache=True)
    r2 = sm.buscar_pixabay("tema cache", session=s, usar_cache=True)
    chamadas = [c for c in s.calls if "pixabay" in c["url"]]
    assert len(chamadas) == 1
    assert r1["candidatos"] == r2["candidatos"]


def test_cache_expirado_apos_24h_refaz_chamada(monkeypatch, tmp_path):
    monkeypatch.setenv("STOCK_MEDIA_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [HIT_PIXABAY]}})
    sm.buscar_pixabay("tema expirado", session=s, usar_cache=True)
    for arquivo in tmp_path.glob("*.json"):
        dado = json.loads(arquivo.read_text(encoding="utf-8"))
        dado["ts"] = time.time() - (25 * 3600)
        arquivo.write_text(json.dumps(dado), encoding="utf-8")
    sm.buscar_pixabay("tema expirado", session=s, usar_cache=True)
    chamadas = [c for c in s.calls if "pixabay" in c["url"]]
    assert len(chamadas) == 2


def test_cache_nao_guarda_chave_da_api(monkeypatch, tmp_path):
    monkeypatch.setenv("STOCK_MEDIA_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-secreta-teste")
    s = _Session({"pixabay": {"hits": [HIT_PIXABAY]}})
    sm.buscar_pixabay("tema sigilo", session=s, usar_cache=True)
    conteudo = "".join(f.read_text(encoding="utf-8") for f in tmp_path.glob("*.json"))
    assert "chave-secreta-teste" not in conteudo
