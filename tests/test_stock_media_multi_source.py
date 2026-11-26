"""Testes das duas fontes de fotos gratuitas. Sem rede real."""
import pytest

from mkt_flow_p0 import stock_media_multi_source as sm


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
        self.calls.append(url)
        if "unsplash" in url:
            return _Resp(self.responses.get("unsplash", {"results": []}))
        if "pixabay" in url:
            return _Resp(self.responses.get("pixabay", {"hits": []}))
        return _Resp({})


def test_unsplash_candidato_valido(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    s = _Session({"unsplash": {"results": [{
        "urls": {"regular": "https://images.unsplash.com/photo-123"},
        "links": {"html": "https://unsplash.com/photos/abc"},
        "user": {"name": "Autor"},
        "width": 1600, "height": 900,
    }]}})
    out = sm.buscar_unsplash("tecnologia", session=s)
    assert len(out["candidatos"]) == 1
    c = out["candidatos"][0]
    assert c["origem"] == "unsplash"
    assert c["revisao_direitos"] == "PENDENTE"


def test_pixabay_candidato_valido(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [{
        "largeImageURL": "https://cdn.pixabay.com/photo/2026/teste.jpg",
        "pageURL": "https://pixabay.com/photos/teste-123/",
        "user": "AutorPixabay", "imageWidth": 1920, "imageHeight": 1080,
    }]}})
    out = sm.buscar_pixabay("tecnologia", session=s)
    assert len(out["candidatos"]) == 1
    c = out["candidatos"][0]
    assert c["origem"] == "pixabay"
    assert c["download_para_servidor"] is True


def test_pixabay_http_rejeitado(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [{
        "largeImageURL": "http://cdn.pixabay.com/photo/x.jpg",
        "pageURL": "https://pixabay.com/photos/x/", "user": "A",
        "imageWidth": 1920, "imageHeight": 1080,
    }]}})
    out = sm.buscar_pixabay("x", session=s)
    assert out["candidatos"] == []


def test_fallback_para_pixabay_quando_unsplash_vazio(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session({"pixabay": {"hits": [{
        "largeImageURL": "https://cdn.pixabay.com/photo/2026/teste.jpg",
        "pageURL": "https://pixabay.com/photos/teste-123/",
        "user": "AutorPixabay", "imageWidth": 1920, "imageHeight": 1080,
    }]}})
    out = sm.buscar_candidatos("tecnologia", session=s)
    assert out["ultima_fonte"] == "pixabay"
    assert any(c["origem"] == "pixabay" for c in out["candidatos"])
    assert out["revisao_direitos"] == "PENDENTE"


def test_sem_chave_pixabay_falha_segura(monkeypatch):
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    out = sm.buscar_pixabay("x", session=_Session({}))
    assert out.get("erro") == "PIXABAY_KEY_AUSENTE"
