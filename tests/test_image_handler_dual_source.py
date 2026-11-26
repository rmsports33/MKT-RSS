"""Integração: buscar_fallback tenta Unsplash e depois Pixabay, sem rede real."""
from mkt_flow_p0 import image_handler as ih
from mkt_flow_p0 import stock_media_multi_source as multi

HIT_PIXABAY = {
    "largeImageURL": "https://pixabay.com/get/ed6a99fd0a76647_1280.jpg",
    "pageURL": "https://pixabay.com/photos/teste-123/",
    "user": "AutorPixabay", "imageWidth": 1920, "imageHeight": 1080,
}


class _Resp:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


class _Session:
    def __init__(self, results=None):
        self.calls = []
        self.results = results if results is not None else {"results": []}

    def get(self, url, **kw):
        self.calls.append(url)
        if "pixabay" in url:
            return _Resp({"hits": [HIT_PIXABAY]})
        return _Resp(self.results)


def _preparar(monkeypatch, session, unsplash_body):
    """Simula a chamada do Unsplash e injeta sessão no Pixabay."""
    def fake_get(url, **kw):
        if "api.unsplash.com" in url:
            return _Resp(unsplash_body)
        raise AssertionError(url)

    monkeypatch.setattr(ih.requests, "get", fake_get)
    original = multi.buscar_pixabay
    monkeypatch.setattr(multi, "buscar_pixabay",
                        lambda tema, timeout=10, **kw: original(
                            tema, timeout=timeout, session=session,
                            usar_cache=False))
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")


def test_fallback_quando_unsplash_nao_tem_resultados(monkeypatch):
    s = _Session()
    _preparar(monkeypatch, s, {"results": []})
    out = ih.buscar_fallback("tecnologia", timeout=5)
    assert out.get("fonte") == "pixabay"
    assert out["candidatos"][0]["origem"] == "pixabay"


def test_fallback_quando_unsplash_tem_resultados_invalidos(monkeypatch):
    s = _Session(results={"results": [{
        "links": {"html": "https://unsplash.com/photos/abc"},
        "urls": {"regular": "https://images.unsplash.com/photo-123"},
        "user": {"name": "Autor"}, "width": 800, "height": 450,
    }]})
    _preparar(monkeypatch, s, s.results)
    out = ih.buscar_fallback("tecnologia", timeout=5)
    assert out.get("fonte") == "pixabay"
    assert any("pixabay" in u for u in s.calls)
