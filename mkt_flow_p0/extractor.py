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


def _texto_documento(html):
    """Preserve product cards / legal headings from the actual fetched HTML.

    Unlike article extraction, this opt-in mode keeps the whole document body.
    Script/metadata and explicitly hidden content are never used as evidence.
    It does not execute JavaScript or claim a rendered-browser observation.
    """
    from lxml import html as lxml_html
    root = lxml_html.fromstring(html)
    for element in list(root.iter()):
        if not isinstance(element.tag, str) or element.getparent() is None:
            continue
        style = re.sub(r"\s+", "", element.get('style', '')).casefold()
        if (element.tag.casefold() in {'head', 'script', 'style', 'noscript', 'template',
                                      'svg', 'nav', 'header', 'footer'}
                or 'hidden' in element.attrib or element.get('aria-hidden', '').casefold() == 'true'
                or 'display:none' in style or 'visibility:hidden' in style):
            element.drop_tree()
    bodies = root.xpath('//body')
    body = bodies[0] if bodies else root
    return re.sub(r'\s+', ' ', ' '.join(body.itertext())).strip()


def _documento_renderizado(url, timeout):
    """Read public page text, including the two NEO plan views; never orders.

    No authenticated browser profile or credentials are used. Only exact plan
    labels may be clicked; checkout, forms and order controls are untouched.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout
    from shutil import which
    with sync_playwright() as playwright:
        executable = which('google-chrome') or which('chromium')
        browser = playwright.chromium.launch(headless=True, executable_path=executable)
        try:
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
            try:
                page.wait_for_load_state('networkidle', timeout=7000)
            except BrowserTimeout:
                pass
            texts = [page.locator('body').inner_text(timeout=5000)]
            from urllib.parse import urlsplit
            target = urlsplit(url)
            if target.hostname in ('www.1x.tech', '1x.tech') and target.path.rstrip('/') == '/order':
                for label in ('Standard', 'Early Access'):
                    selector = page.get_by_text(label, exact=True)
                    if selector.count() == 1 and selector.is_visible():
                        selector.click(timeout=3000)
                        texts.append(page.locator('body').inner_text(timeout=5000))
            return {'texto': '\n\n'.join(dict.fromkeys(texts)), 'titulo': page.title(),
                    'final_url': page.url}
        finally:
            browser.close()


def extrair_conteudo(url: str, timeout: int = 20, min_palavras: int = MIN_PALAVRAS_OK,
                    preservar_documento: bool = False, renderizar: bool = False) -> dict:
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

    if renderizar:
        try:
            rendered = _documento_renderizado(url, timeout)
            palavras = contar_palavras(rendered['texto'])
            return {**rendered, 'url': url, 'palavras': palavras,
                    'qualidade_ok': palavras >= min_palavras, 'origem': 'playwright_documento'}
        except Exception:
            return {'erro': 'Pagina renderizada indisponivel; nao substituir por fatos do briefing'}

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
    if contar_palavras(texto) < min_palavras:
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

    if preservar_documento:
        try:
            texto = _texto_documento(downloaded)
        except Exception:
            return {"erro": "Falha ao extrair documento completo"}

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
        "origem": "html_documento" if preservar_documento else "trafilatura",
    }


def extrair_completo(url: str, **kwargs) -> dict:
    """Alias explícito para pipeline: fetch + extract + metadata."""
    return extrair_conteudo(url, **kwargs)
