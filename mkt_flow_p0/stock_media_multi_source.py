"""Busca de fotos gratuitas em DUAS fontes, com contrato comum.

Fontes:
  1. Unsplash (chave UNSPLASH_ACCESS_KEY — já no projeto)
  2. Pixabay (chave PIXABAY_API_KEY — criar conta gratuita)

Regras oficiais da API Pixabay (documentação conferida em 26/11/2026):
- respostas devem ficar em cache por 24 horas;
- não hotlink permanente: baixar a imagem para o servidor antes de usar;
- exibir a origem da imagem quando os resultados são mostrados;
- parâmetro lang aceita "pt"; parâmetro q limitado a 100 caracteres.

Regras do projeto:
- Nunca promover candidato a imagem licenciada automaticamente.
- Exigir revisão humana de direitos e de enquadramento.
- URLs HTTPS, domínios fixos, tamanho mínimo 1200x675 (tamanho da capa).
- Nenhuma escrita no WordPress aqui. Apenas busca e validação.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from urllib.parse import urlsplit

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
MIN_W, MIN_H = 1200, 675
MAX_Q_CHARS = 100
CACHE_TTL_SEGUNDOS = 24 * 60 * 60


def _cache_dir() -> "Path":
    return Path(os.getenv("STOCK_MEDIA_CACHE_DIR") or
                (Path(tempfile.gettempdir()) / "mkt-rss-stock-cache"))


def _chave_cache(fonte, params):
    """Chave estável sem incluir segredos (key/headers)."""
    base = {"fonte": fonte}
    base.update({k: v for k, v in params.items()
                 if k not in ("key", "Authorization", "headers")})
    raw = json.dumps(base, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_ler(chave):
    if not chave:
        return None
    try:
        dado = json.loads((_cache_dir() / (chave + ".json")).read_text(encoding="utf-8"))
        if (isinstance(dado, dict) and isinstance(dado.get("ts"), (int, float))
                and time.time() - dado["ts"] < CACHE_TTL_SEGUNDOS
                and isinstance(dado.get("body"), dict)):
            return dado["body"]
    except (OSError, ValueError, TypeError):
        pass
    return None


def _cache_gravar(chave, body):
    if not chave:
        return
    try:
        destino = _cache_dir()
        destino.mkdir(parents=True, exist_ok=True)
        (destino / (chave + ".json")).write_text(
            json.dumps({"ts": time.time(), "body": body}, ensure_ascii=False),
            encoding="utf-8")
    except OSError:
        pass


def _host_ok(url, host, prefix="/"):
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and (p.hostname or "").lower() == host
                and p.port in (None, 443) and not p.username and not p.password
                and not p.fragment and p.path.startswith(prefix))
    except ValueError:
        return False


def _url_pixabay_ok(url):
    # largeImageURL vem de pixabay.com/get/...; previewURL de cdn.pixabay.com/photo/...
    return (_host_ok(url, "pixabay.com", "/get/")
            or _host_ok(url, "cdn.pixabay.com", "/photo/"))


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
        if not (_url_pixabay_ok(url) and _host_ok(pagina, "pixabay.com", "/")):
            return None
        licenca_url = PIXABAY_LICENSE
    else:
        return None
    autor = autor.strip()
    return {
        "url": url, "pagina_origem": pagina, "autor": autor,
        "licenca_url": licenca_url, "origem": fonte,
        "largura": w, "altura": h,
        "alt_text": foto.get("alt_text") or "Imagem editorial de tecnologia",
        "credito_exibicao": f"Foto: {autor} / {fonte.capitalize()}",
        "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE",
        "download_para_servidor": fonte == "pixabay",
    }


def buscar_unsplash(tema, *, timeout=10, session=None, usar_cache=True):
    _load_env()
    key = (os.getenv("UNSPLASH_ACCESS_KEY") or "").strip()
    if not key:
        return {"erro": "UNSPLASH_KEY_AUSENTE"}
    tema = (tema or "").strip()[:MAX_Q_CHARS]
    params = {"query": tema, "per_page": 5, "orientation": "landscape"}
    chave = _chave_cache("unsplash", params) if usar_cache else None
    body = _cache_ler(chave)
    if body is None:
        http = session or requests
        try:
            r = http.get("https://api.unsplash.com/search/photos", params=params,
                         headers={"Authorization": f"Client-ID {key}"},
                         timeout=timeout)
            r.raise_for_status()
            body = r.json()
        except Exception as exc:
            return {"erro": f"UNSPLASH_FALHA: {type(exc).__name__}"}
        _cache_gravar(chave, body)
    candidatos = []
    for foto in (body.get("results") or []):
        item = _normalizar_foto({
            "url": (foto.get("urls") or {}).get("regular"),
            "pagina_origem": (foto.get("links") or {}).get("html"),
            "autor": (foto.get("user") or {}).get("name"),
            "largura": foto.get("width"), "altura": foto.get("height"),
        }, "unsplash")
        if item:
            candidatos.append(item)
    return {"candidatos": candidatos, "origem": "unsplash"}


def buscar_pixabay(tema, *, timeout=10, session=None, usar_cache=True):
    _load_env()
    key = (os.getenv("PIXABAY_API_KEY") or "").strip()
    if not key:
        return {"erro": "PIXABAY_KEY_AUSENTE"}
    tema = (tema or "").strip()[:MAX_Q_CHARS]
    # q NÃO é pré-codificado: requests codifica uma vez. quote_plus causaria dupla codificação.
    params = {"q": tema, "image_type": "photo", "orientation": "horizontal",
              "min_width": MIN_W, "min_height": MIN_H, "safesearch": "true",
              "per_page": 5, "lang": "pt"}
    chave = _chave_cache("pixabay", params) if usar_cache else None
    body = _cache_ler(chave)
    if body is None:
        http = session or requests
        try:
            r = http.get("https://pixabay.com/api/", params={**params, "key": key},
                         timeout=timeout)
            r.raise_for_status()
            body = r.json()
        except Exception as exc:
            return {"erro": f"PIXABAY_FALHA: {type(exc).__name__}"}
        _cache_gravar(chave, body)
    candidatos = []
    for hit in (body.get("hits") or []):
        item = _normalizar_foto({
            "url": hit.get("largeImageURL") or hit.get("webformatURL"),
            "pagina_origem": hit.get("pageURL"),
            "autor": hit.get("user"),
            "largura": hit.get("imageWidth"), "altura": hit.get("imageHeight"),
            "alt_text": hit.get("tags"),
        }, "pixabay")
        if item:
            candidatos.append(item)
    return {"candidatos": candidatos, "origem": "pixabay"}


def buscar_candidatos(tema, *, timeout=10, session=None, usar_cache=True):
    """Tenta Unsplash e, se vazio/falha, Pixabay. Nunca aprova nada."""
    out = {"tema": tema, "fontes_tentadas": [], "candidatos": [],
           "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE",
           "wordpress_written": False}
    for nome, func in (("unsplash", buscar_unsplash), ("pixabay", buscar_pixabay)):
        out["fontes_tentadas"].append(nome)
        res = func(tema, timeout=timeout, session=session, usar_cache=usar_cache)
        if isinstance(res, dict) and res.get("candidatos"):
            out["candidatos"].extend(res["candidatos"])
            out["ultima_fonte"] = nome
            break
        if isinstance(res, dict) and res.get("erro"):
            out.setdefault("erros", {})[nome] = res["erro"]
    if not out["candidatos"]:
        out["proxima_etapa"] = "PESQUISA_BANCO_PENDENTE"
    return out
