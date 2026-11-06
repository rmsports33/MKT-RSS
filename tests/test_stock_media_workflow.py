"""Teste E2E offline (REST simulado) do upload supervisionado e readback."""
import io
from unittest.mock import patch
from PIL import Image

from mkt_flow_p0.stock_media_workflow import (
    associar_foto_gratuita_a_rascunho, validar_escolha
)

PHOTO = {
    "url": "https://images.unsplash.com/photo-1688039763740-9036cb5d566e",
    "pagina_origem": "https://unsplash.com/photos/a-microphone-in-front-of-a-computer-monitor-O6B3_2ylHLo",
    "autor": "Koen Sweers", "licenca_url": "https://unsplash.com/license",
    "revisao_direitos": "APROVADO_PELO_EDITOR",
    "revisao_visual": "APROVADO_PELO_EDITOR",
    "alt_text": "Microfone em estúdio de gravação",
}


def _picture():
    b = io.BytesIO()
    Image.new("RGB", (1800, 1100), "white").save(b, format="JPEG")
    return b.getvalue()


class Response:
    def __init__(self, status, data=None, headers=None, image=None):
        self.status_code = status
        self._data = data
        self.headers = headers or {}
        self._image = image

    def json(self):
        return self._data

    def iter_content(self, size):
        for x in range(0, len(self._image), size):
            yield self._image[x:x+size]


class Client:
    def __init__(self, *, post_status="draft", existing_media=0):
        self.post_status = post_status
        self.featured = existing_media
        self.calls = []
        self.created = None

    def get(self, url, **kwargs):
        self.calls.append(("GET", url))
        if url.endswith("/posts/9769"):
            return Response(200, {"id": 9769, "status": self.post_status,
                                  "featured_media": self.featured})
        if url.startswith("https://images.unsplash.com/"):
            return Response(200, headers={"Content-Type": "image/jpeg"},
                            image=_picture())
        raise AssertionError(url)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url))
        if url.endswith("/media"):
            self.created = kwargs["data"]
            return Response(201, {"id": 12345})
        if url.endswith("/media/12345"):
            self.metadata = kwargs["json"]
            return Response(200, {"id": 12345})
        if url.endswith("/posts/9769"):
            self.featured = kwargs["json"]["featured_media"]
            return Response(200, {"id": 9769, "status": "draft"})
        raise AssertionError(url)


def run(client, photo=None):
    return associar_foto_gratuita_a_rascunho(
        photo or PHOTO, post_id=9769,
        wp_url="https://conexotech.com.br", wp_user="editor",
        wp_app_password="test-password-not-real", request_client=client)


def test_imagem_gratuita_aprovada_gera_1200x675_e_readback():
    cl = Client()
    result = run(cl)
    assert result["status"] == "CAPA_ASSOCIADA_A_DRAFT"
    assert result["media_id"] == 12345
    img = Image.open(io.BytesIO(cl.created))
    assert img.size == (1200, 675)
    assert "Koen Sweers" in cl.metadata["caption"]
    assert PHOTO["pagina_origem"] in cl.metadata["description"]
    assert PHOTO["licenca_url"] in cl.metadata["description"]
    assert cl.metadata["alt_text"] == PHOTO["alt_text"]
    assert cl.calls[-1] == ("GET", "https://conexotech.com.br/wp-json/wp/v2/posts/9769")


def test_sem_aprovacao_humana_nao_usa_rede():
    photo = dict(PHOTO, revisao_visual="PENDENTE")
    cl = Client()
    result = run(cl, photo)
    assert result["status"] == "BLOQUEADO"
    assert cl.calls == []


def test_imagem_rss_ou_url_insegura_bloqueada_sem_rede():
    for url in ("https://publisher.test/image.jpg",
                "http://images.unsplash.com/photo-x",
                "https://images.unsplash.com.evil.test/photo-x",
                "https://images.unsplash.com/photo-x#fragment"):
        cl = Client()
        result = run(cl, dict(PHOTO, url=url))
        assert result["status"] == "BLOQUEADO"
        assert cl.calls == []


def test_post_publicado_nao_recebe_imagem():
    cl = Client(post_status="publish")
    assert run(cl)["motivo"] == "post_nao_e_draft"
    assert len(cl.calls) == 1


def test_nao_substituir_imagem_existente():
    cl = Client(existing_media=9776)
    assert run(cl)["motivo"] == "post_ja_possui_imagem"
    assert len(cl.calls) == 1


def test_falha_no_download_nao_escreve_wp():
    cl = Client()
    original = cl.get
    def failing(url, **kwargs):
        if url.startswith("https://images.unsplash.com/"):
            cl.calls.append(("GET", url))
            return Response(302)
        return original(url, **kwargs)
    cl.get = failing
    result = run(cl)
    assert result["motivo"] == "imagem_invalida"
    assert not any(method == "POST" for method, _ in cl.calls)


def test_licenca_ou_referencia_invalida_bloqueia():
    for patch in ({"licenca_url": "https://example.com/license"},
                  {"pagina_origem": "https://evil.test/foo"},
                  {"autor": ""}):
        cl = Client()
        assert run(cl, dict(PHOTO, **patch))["status"] == "BLOQUEADO"
        assert cl.calls == []
