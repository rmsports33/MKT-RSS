"""Integração: buscar_fallback tenta Unsplash e depois Pixabay."""
from mkt_flow_p0 import image_handler as ih


class _Resp:
    def __init__(self, body):
        self._body = body
    def raise_for_status(self):
        return None
    def json(self):
        return self._body


class _Session:
    def __init__(self):
        self.calls = []
    def get(self, url, **kw):
        self.calls.append(url)
        if "unsplash" in url:
            return _Resp({"results": []})  # vazio -> deve cair no Pixabay
        if "pixabay" in url:
            return _Resp({"hits": [{
                "largeImageURL": "https://cdn.pixabay.com/photo/2026/teste.jpg",
                "pageURL": "https://pixabay.com/photos/teste-123/",
                "user": "AutorPixabay", "imageWidth": 1920, "imageHeight": 1080,
            }]})
        return _Resp({})


def test_buscar_fallback_cai_para_pixabay(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "chave-teste")
    monkeypatch.setenv("PIXABAY_API_KEY", "chave-teste")
    s = _Session()
    # Injeta sessão no módulo de busca dupla (usada no fallback)
    import mkt_flow_p0.stock_media_multi_source as multi
    original = multi.buscar_pixabay
    monkeypatch.setattr(multi, "buscar_pixabay",
                        lambda tema, timeout=10: original(tema, timeout=timeout, session=s))
    out = ih.buscar_fallback("tecnologia", timeout=5)
    assert out.get("fonte") == "pixabay"
    assert out["candidatos"][0]["origem"] == "pixabay"
