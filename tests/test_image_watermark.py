"""Testes da marca d'água ConexoTech. Sem rede, sem WordPress."""
from pathlib import Path

from PIL import Image
import pytest

from mkt_flow_p0.image_watermark import aplicar_marca, SELO


def _imagem(tmp_path, cor=(120, 140, 160), tamanho=(640, 360)):
    p = tmp_path / "base.jpg"
    Image.new("RGB", tamanho, cor).save(p, quality=92)
    return p


def test_aplica_marca_e_salva(tmp_path):
    src = _imagem(tmp_path)
    out = tmp_path / "marcada.jpg"
    r = aplicar_marca(src, out)
    assert r["aplicado"] is True
    assert out.exists()
    assert r["marca_propria"] is True
    assert r["terceiros"] is False
    assert r["posicao"] == "inferior_direita"


def test_texto_padrao_e_conexotech():
    assert SELO == "ConexoTech"


def test_marca_altera_pixels_no_canto_inferior_direito(tmp_path):
    src = _imagem(tmp_path)
    out = tmp_path / "marcada.jpg"
    aplicar_marca(src, out)
    a, b = Image.open(src).convert("RGB"), Image.open(out).convert("RGB")
    # Região do selo (canto inferior direito) deve mudar.
    reg_a = a.crop((a.width - 200, a.height - 60, a.width, a.height))
    reg_b = b.crop((b.width - 200, b.height - 60, b.width, b.height))
    assert list(reg_a.get_flattened_data()) != list(reg_b.get_flattened_data())


def test_canto_superior_esquerdo_permanece_igual(tmp_path):
    src = _imagem(tmp_path)
    out = tmp_path / "marcada.jpg"
    aplicar_marca(src, out)
    a, b = Image.open(src).convert("RGB"), Image.open(out).convert("RGB")
    canto = (0, 0, 100, 60)
    assert list(a.crop(canto).get_flattened_data()) == list(b.crop(canto).get_flattened_data())


def test_texto_customizado(tmp_path):
    src = _imagem(tmp_path)
    out = tmp_path / "marcada.jpg"
    r = aplicar_marca(src, out, texto="MeuSeloTeste")
    assert r["selo"] == "MeuSeloTeste"


def test_entrada_ausente_bloqueia(tmp_path):
    with pytest.raises(ValueError, match="WATERMARK_INPUT_MISSING"):
        aplicar_marca(tmp_path / "nao_existe.jpg", tmp_path / "out.jpg")
