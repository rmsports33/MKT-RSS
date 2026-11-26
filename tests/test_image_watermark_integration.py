"""Integração: prepare_assets aplica a marca antes dos recortes."""
import io
from PIL import Image

from mkt_flow_p0.image_protocol import prepare_assets


def _resource():
    return {
        "id": "watermark-test-001",
        "source_page": "https://unsplash.com/photos/teste",
        "image_url": "https://images.unsplash.com/photo-teste",
        "author": "Autor Teste",
        "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "checked_at": "2026-11-26T10:00:00Z",
        "alt": "Imagem de teste para marca dagua",
        "caption": "Foto de teste com credito documentado",
        "credit": "Autor Teste / Unsplash",
        "rights_review": "DOCUMENTED_SOURCE_CHECK",
    }


def _imagem_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (1600, 900), (100, 120, 140)).save(buf, "JPEG", quality=92)
    return buf.getvalue()


def test_prepare_assets_aplica_marca_nos_recortes():
    out = prepare_assets(_resource(), _imagem_bytes())
    assert "watermark" in out
    assert out["watermark"]["aplicado"] is True
    assert out["watermark"]["selo"] == "ConexoTech"
    assert out["watermark"]["marca_propria"] is True
    assert "desktop" in out["assets"] and "mobile" in out["assets"]
    # original_sha256 preserva os bytes antes da marca
    assert out["original_sha256"] != out["assets"]["desktop"]["sha256"]
