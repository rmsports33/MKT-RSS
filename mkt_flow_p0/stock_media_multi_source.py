"""Busca de fotos gratuitas em DUAS fontes, com contrato comum.

Fontes:
  1. Unsplash (chave UNSPLASH_ACCESS_KEY — já no projeto)
  2. Pixabay (chave PIXABAY_API_KEY — criar conta gratuita)

Regras:
- Nunca promover candidato a imagem licenciada automaticamente.
- Exigir revisão humana de direitos e de enquadramento.
- URLs HTTPS, domínios fixos, tamanho mínimo 1440x810.
- Pixabay: baixar para o servidor (a API proíbe hotlink permanente).
- Nenhuma escrita no WordPress aqui. Apenas busca e validação.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit, quote_plus

import requests

# Reusa o carregador de .env existente, sem duplicar lógica.
try:
    from dotenv import load_dotenv
    from pathlib import Path
    def _load_env():
        root = Path(__file__).resolve().parent.parent
        for p in (root / ".env", Path.cwd() / ".env"):
            if p.exists():
                load_dotenv(p, override=False)
except Exception:
    def _load_env():
        return None


UNSPLASH_LICENSE = "https://unsplash.com/license"
PIXABAY_LICENSE = "https://pixabay.com/service/license-summary/"
MIN_W, MIN_H = 1440, 810


def _host_ok(url, host, prefix="/"):
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and (p.hostname or "").lower() == host
                and p.port in (None, 443) and not p.username and not p.password
                and not p.fragment and p.path.startswith(prefix))
    except ValueError:
        return False


def _normalizar_foto(foto, fonte):
    """Normaliza candidato para o contrato comum; None se inválido."""
    if not isinstance(foto, dict):
        return None
    url, pagina = foto.get("url"), foto.get("pagina_origem")
    autor, licenca_url = foto.get("autor"), foto.get("licenca_url")
    w, h = foto.get("largura"), foto.get("altura")
    if not (isinstance(w, int) and isinstance(h, int) and w >= MIN_W and h >= MIN_H):
        return None
    if not (isinstance(autor, str) and autor.strip()):
        return None
    if fonte == "unsplash":
        if not (_host_ok(url, "images.unsplash.com", "/photo-")
                and _host_ok(pagina, "unsplash.com", "/photos/")):
            return None
        licenca_url = UNSPLASH_LICENSE
    elif fonte == "pixabay":
        if not (_host_ok(url, "cdn.pixabay.com", "/photo/")
                and _host_ok(pagina, "pixabay.com", "/")):
            return None
        licenca_url = PIXABAY_LICENSE
    else:
        return None
    return {
        "url": url, "pagina_origem": pagina, "autor": autor.strip(),
        "licenca_url": licenca_url, "origem": fonte,
        "largura": w, "altura": h,
        "alt_text": foto.get("alt_text") or "Imagem editorial de tecnologia",
        "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE",
        "download_para_servidor": fonte == "pixabay",
    }


def buscar_unsplash(tema, *, timeout=10, session=None):
    _load_env()
    key = (os.getenv("UNSPLASH_ACCESS_KEY") or "").strip()
    if not key:
        return {"erro": "UNSPLASH_KEY_AUSENTE"}
    http = session or requests
    try:
        r = http.get("https://api.unsplash.com/search/photos",
                     params={"query": tema, "per_page": 5, "orientation": "landscape"},
                     headers={"Authorization": f"Client-ID {key}"}, timeout=timeout)
        r.raise_for_status()
    except Exception as exc:
        return {"erro": f"UNSPLASH_FALHA: {type(exc).__name__}"}
    candidatos = []
    for foto in (r.json().get("results") or []):
        item = _normalizar_foto({
            "url": (foto.get("urls") or {}).get("regular"),
            "pagina_origem": (foto.get("links") or {}).get("html"),
            "autor": (foto.get("user") or {}).get("name"),
            "largura": foto.get("width"), "altura": foto.get("height"),
        }, "unsplash")
        if item:
            candidatos.append(item)
    return {"candidatos": candidatos, "origem": "unsplash"}


def buscar_pixabay(tema, *, timeout=10, session=None):
    _load_env()
    key = (os.getenv("PIXABAY_API_KEY") or "").strip()
    if not key:
        return {"erro": "PIXABAY_KEY_AUSENTE"}
    http = session or requests
    try:
        r = http.get("https://pixabay.com/api/",
                     params={"key": key, "q": quote_plus(tema), "image_type": "photo",
                             "orientation": "horizontal", "min_width": MIN_W,
                             "min_height": MIN_H, "safesearch": "true", "per_page": 5},
                     timeout=timeout)
        r.raise_for_status()
    except Exception as exc:
        return {"erro": f"PIXABAY_FALHA: {type(exc).__name__}"}
    candidatos = []
    for hit in (r.json().get("hits") or []):
        item = _normalizar_foto({
            "url": hit.get("largeImageURL") or hit.get("webformatURL"),
            "pagina_origem": hit.get("pageURL"),
            "autor": hit.get("user"),
            "largura": hit.get("imageWidth"), "altura": hit.get("imageHeight"),
        }, "pixabay")
        if item:
            candidatos.append(item)
    return {"candidatos": candidatos, "origem": "pixabay"}


def buscar_candidatos(tema, *, timeout=10, session=None):
    """Tenta Unsplash e, se vazio/falha, Pixabay. Nunca approve nada."""
    out = {"tema": tema, "fontes_tentadas": [], "candidatos": [],
           "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE",
           "wordpress_written": False}
    for nome, func in (("unsplash", buscar_unsplash), ("pixabay", buscar_pixabay)):
        out["fontes_tentadas"].append(nome)
        res = func(tema, timeout=timeout, session=session)
        if isinstance(res, dict) and res.get("candidatos"):
            out["candidatos"].extend(res["candidatos"])
            out["ultima_fonte"] = nome
            break
        if isinstance(res, dict) and res.get("erro"):
            out.setdefault("erros", {})[nome] = res["erro"]
    if not out["candidatos"]:
        out["proxima_etapa"] = "PESQUISA_BANCO_PENDENTE"
    return out
