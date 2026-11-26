"""Marca d'água ConexoTech aplicada AFTER geração/seleção, BEFORE upload.

Padrão aprovado:
- Texto: "ConexoTech"
- Posição: canto inferior direito
- Estilo: branco com sombra leve, discreto (~3.2% da altura)
- Aplica a TODAS as capas (geradas e de banco)

Nunca altera a proveniência da imagem: o selo é Own-brand, não de terceiros.
Respeita a regra existente `PASS_NO_THIRD_PARTY_BRANDING` do image_protocol.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SELO = "ConexoTech"
_MARGEM = 0.035          # 3.5% da menor dimensão
_TAMANHO = 0.032         # ~3.2% da altura da imagem


def _fonte(tamanho: int):
    """Tenta fontes comuns; fallback para a padrão do Pillow."""
    candidatas = (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidatas:
        try:
            return ImageFont.truetype(path, tamanho)
        except (OSError, ValueError):
            continue
    return ImageFont.load_default()


def aplicar_marca(entrada, saida=None, *, texto: str = SELO) -> dict:
    """Aplica o selo e salva em `saida`.

    Se `saida` for None, substitui o arquivo de entrada (cuidado: use com
    arquivo temporário). Devolve dict com metadados da operação — sem segredos.
    """
    src = Path(entrada)
    if not src.exists():
        raise ValueError("WATERMARK_INPUT_MISSING")
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    tamanho = max(12, int(h * _TAMANHO))
    fonte = _fonte(tamanho)

    # Medidas do texto
    tmp = ImageDraw.Draw(img)
    try:
        box = tmp.textbbox((0, 0), texto, font=fonte)
        tw, th = box[2] - box[0], box[3] - box[1]
    except AttributeError:
        tw, th = tmp.textsize(texto, font=fonte)

    margem = max(6, int(min(w, h) * _MARGEM))
    x = w - tw - margem
    y = h - th - margem

    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(camada)

    # Sombra leve (4 deslocamentos) para legibilidade em fundos claros/escuros.
    sombra = (0, 0, 0, 120)
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        draw.text((x + dx, y + dy), texto, font=fonte, fill=sombra)

    # Texto branco com leve transparência (discreto).
    draw.text((x, y), texto, font=fonte, fill=(255, 255, 255, 220))

    final = Image.alpha_composite(img, camada).convert("RGB")
    destino = Path(saida) if saida else src
    destino.parent.mkdir(parents=True, exist_ok=True)
    final.save(destino, quality=92)

    return {
        "aplicado": True,
        "selo": texto,
        "posicao": "inferior_direita",
        "tamanho_px": [w, h],
        "fonte_px": tamanho,
        "marca_propria": True,
        "terceiros": False,
        "destino": str(destino),
    }
