"""
mkt_flow_p0.image_handler — Pipeline de capa (P0).
Padrão ConexoTech 1200x675 JPEG (cover crop centralizado). Sem IA paga:
usa a imagem original da matéria; fallback Unsplash/Pexels só com key free.

Benchmark: AINP/AutoBlog cobram Pro por "AI image/Imagen"; DALL-E custa
$0.04-0.08/foto. Aqui: Pillow local (grátis) + upload via wp/v2/media.
Env lido sob demanda (sem side-effect no import).
"""
import io
import logging
import os
from urllib.parse import quote_plus

import requests

logger = logging.getLogger("image_handler")

CAPA_LARGURA, CAPA_ALTURA = 1200, 675
QUALIDADE_JPEG = 82
HEADERS = {"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 imagens)"}
MAX_BYTES = 8 * 1024 * 1024


def baixar_imagem(url: str, timeout: int = 15) -> dict:
    """Baixa imagem. Retorna {bytes, content_type} ou {"erro":...}. Teto 8MB."""
    url = (url or "").strip()
    if not url.startswith("http"):
        return {"erro": "URL de imagem inválida"}
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, stream=True)
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype and not ctype.startswith("image/"):
            return {"erro": f"URL não é imagem (Content-Type: {ctype})"}
        buf = io.BytesIO()
        total = 0
        for chunk in r.iter_content(256 * 1024):
            total += len(chunk)
            if total > MAX_BYTES:
                return {"erro": "Imagem acima de 8MB — ignorada"}
            buf.write(chunk)
        return {"bytes": buf.getvalue(), "content_type": ctype or "image/jpeg"}
    except requests.Timeout:
        return {"erro": f"Download timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha no download: {str(e)[:120]}"}


def processar_capa(imagem_bytes: bytes, largura: int = CAPA_LARGURA, altura: int = CAPA_ALTURA,
                   qualidade: int = QUALIDADE_JPEG) -> dict:
    """Cover crop centralizado + JPEG. Retorna {bytes, largura, altura} ou {"erro":...}."""
    try:
        from PIL import Image
    except ImportError:
        return {"erro": "Pillow não instalado — rode: pip install Pillow"}
    try:
        img = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    except Exception as e:
        return {"erro": f"Imagem ilegível: {str(e)[:100]}"}
    # Cover: escala para cobrir e corta centro
    proporcao = max(largura / img.width, altura / img.height)
    nova = img.resize((round(img.width * proporcao), round(img.height * proporcao)))
    x = (nova.width - largura) // 2
    y = (nova.height - altura) // 2
    capa = nova.crop((x, y, x + largura, y + altura))
    buf = io.BytesIO()
    capa.save(buf, format="JPEG", quality=qualidade, optimize=True)
    return {"bytes": buf.getvalue(), "largura": largura, "altura": altura, "content_type": "image/jpeg"}


def buscar_fallback(consulta: str, timeout: int = 10) -> dict:
    """Banco gratuito (Unsplash com key free). Sem key → erro orientando a colar imagem."""
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        _r = Path(__file__).parent.parent
        for _p in [_r / ".env", Path.cwd() / ".env"]:
            if _p.exists():
                load_dotenv(_p, override=False)
    except Exception:
        pass
    key = (os.getenv("UNSPLASH_ACCESS_KEY") or "").strip()
    if not key:
        return {"erro": "Sem imagem original e sem UNSPLASH_ACCESS_KEY — cole a imagem manualmente"}
    try:
        r = requests.get("https://api.unsplash.com/search/photos",
                         params={"query": consulta, "per_page": 1, "orientation": "landscape"},
                         headers={"Authorization": f"Client-ID {key}"}, timeout=timeout)
        r.raise_for_status()
        resultados = (r.json().get("results") or [])
        if not resultados:
            return {"erro": f"Unsplash sem resultado para '{consulta}'"}
        foto = resultados[0]
        return {"url": (foto.get("urls") or {}).get("regular", ""),
                "autor": ((foto.get("user") or {}).get("name") or ""),
                "origem": "unsplash"}
    except Exception as e:
        return {"erro": f"Unsplash falhou: {str(e)[:120]}"}


def preparar_capa(url_original: str = "", consulta_fallback: str = "", timeout: int = 15) -> dict:
    """Fluxo completo: original → processada; se falhar, tenta fallback gratuito."""
    if url_original:
        dl = baixar_imagem(url_original, timeout=timeout)
        if "bytes" in dl:
            capa = processar_capa(dl["bytes"])
            if "bytes" in capa:
                capa["origem"] = "original"
                return capa
            logger.warning(f"capa original ilegível, tentando fallback: {capa.get('erro')}")
    if consulta_fallback:
        fb = buscar_fallback(consulta_fallback, timeout=timeout)
        if fb.get("url"):
            dl = baixar_imagem(fb["url"], timeout=timeout)
            if "bytes" in dl:
                capa = processar_capa(dl["bytes"])
                if "bytes" in capa:
                    capa["origem"] = "unsplash"
                    capa["credito"] = f"Foto: {fb.get('autor', '')} / Unsplash"
                    return capa
    return {"erro": "Sem capa: original falhou e fallback indisponível"}
