"""
mkt_flow_p0.extractor — Extração full-text própria (P0)
Substitui "Advanced Scraper Pro" dos plugins (AINP/AutoBlog).
Resolve posts curtinhos (28-46 palavras): baixa HTML e extrai corpo com Trafilatura.

Benchmark: Trafilatura (Apache 2.0, F1 ~0.945, usada por HuggingFace/IBM)
primeira opção para news/blog; fallback recall para páginas curtas.
Sem browser, sem custo por página. Timeout + validação mínima de 400 palavras.
"""
import logging
import re

import requests

logger = logging.getLogger("extractor")

MIN_PALAVRAS_OK = 400

_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (MKT-Flow-P0 extractor)"})

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:
    trafilatura = None  # type: ignore
    _HAS_TRAFILATURA = False


def contar_palavras(texto: str) -> int:
    return len(re.findall(r"\S+", texto or ""))


def extrair_conteudo(url: str, timeout: int = 20, min_palavras: int = MIN_PALAVRAS_OK) -> dict:
    """
    Baixa URL e extrai artigo em Markdown.
    Retorna {titulo, texto, autor, data, imagem, palavras, qualidade_ok, origem}
    ou {"erro":...}. Nunca retorna excerpt como se fosse texto completo:
    se < min_palavras, qualidade_ok=False (chamador decide descartar).
    """
    if not _HAS_TRAFILATURA:
        return {"erro": "trafilatura não instalada — rode: pip install trafilatura"}

    url = (url or "").strip()
    if not url.startswith("http"):
        return {"erro": f"URL inválida: '{url[:60]}'"}

    # Download via requests (UA realista) — mais confiável que fetch_url
    # padrão em sites BR com Cloudflare (ex.: Tecnoblog vinha 0 palavras).
    html = ""
    try:
        resp = _session.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except requests.Timeout:
        return {"erro": f"Página timeout após {timeout}s"}
    except Exception as e:
        logger.warning(f"extractor requests falhou {url[:80]}: {e}")
        # Fallback: tenta fetch_url da trafilatura
        try:
            html = trafilatura.fetch_url(url) or ""
        except Exception:
            return {"erro": f"Falha ao baixar página: {str(e)[:120]}"}

    if not html or len(html) < 500:
        return {"erro": "Página vazia ou bloqueada (403/JS pesado) — tente outra matéria"}

    downloaded = html
    texto = ""
    meta: dict = {}
    try:
        texto = trafilatura.extract(
            downloaded,
            output_format="markdown",
            include_comments=False,
            include_tables=True,
        ) or ""
    except Exception as e:
        logger.warning(f"extractor extract falhou: {e}")

    # Fallback recall para páginas curtas (produto com 2 frases, etc.)
    if contar_palavras(texto) < 100:
        try:
            fb = trafilatura.extract(
                downloaded,
                output_format="markdown",
                include_comments=False,
                include_tables=True,
                favor_recall=True,
            ) or ""
            if contar_palavras(fb) > contar_palavras(texto):
                texto = fb
        except Exception:
            pass

    try:
        m = trafilatura.extract_metadata(downloaded)
        if m:
            meta = {
                "titulo": getattr(m, "title", "") or "",
                "autor": getattr(m, "author", "") or "",
                "data": getattr(m, "date", "") or "",
                "imagem": getattr(m, "image", "") or "",
                "descricao": getattr(m, "description", "") or "",
                "site": getattr(m, "sitename", "") or "",
            }
    except Exception as e:
        logger.warning(f"extractor metadata falhou: {e}")

    palavras = contar_palavras(texto)
    return {
        "url": url,
        "titulo": meta.get("titulo", ""),
        "texto": texto,
        "autor": meta.get("autor", ""),
        "data": meta.get("data", ""),
        "imagem": meta.get("imagem", ""),
        "descricao": meta.get("descricao", ""),
        "site": meta.get("site", ""),
        "palavras": palavras,
        "qualidade_ok": palavras >= min_palavras,
        "origem": "trafilatura",
    }


def extrair_completo(url: str, **kwargs) -> dict:
    """Alias explícito para pipeline: fetch + extract + metadata."""
    return extrair_conteudo(url, **kwargs)
