"""
Testes P0 — image_handler (offline, imagem gerada em memória)
pytest tests/test_image_handler_p0.py -v
"""
import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from mkt_flow_p0.image_handler import processar_capa, baixar_imagem, preparar_capa


def _foto_fake(w=1600, h=900, cor=(20, 40, 80)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), cor).save(buf, format="JPEG")
    return buf.getvalue()


def test_capa_1200x675_jpeg():
    r = processar_capa(_foto_fake())
    assert (r["largura"], r["altura"]) == (1200, 675)
    assert r["bytes"][:2] == b"\xff\xd8"  # magic JPEG


def test_capa_vertical_corta_centro():
    r = processar_capa(_foto_fake(600, 1200))
    assert (r["largura"], r["altura"]) == (1200, 675)


def test_imagem_ilegiven_erro():
    assert "erro" in processar_capa(b"nao-e-imagem")


def test_baixar_recusa_nao_imagem():
    m = MagicMock()
    m.headers = {"Content-Type": "text/html"}
    m.raise_for_status.return_value = None
    m.iter_content.return_value = [b"<html>"]
    with patch("mkt_flow_p0.image_handler.requests.get", return_value=m):
        assert "erro" in baixar_imagem("https://x.com/pag")


def test_preparar_sem_nada_erro_claro():
    with patch("mkt_flow_p0.image_handler.buscar_fallback", return_value={"erro": "x"}):
        r = preparar_capa(url_original="", consulta_fallback="fone")
        assert "erro" in r
