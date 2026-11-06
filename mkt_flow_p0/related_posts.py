"""Links internos reais obtidos SOMENTE de posts publicados no WordPress.

Sem usar ferramentas de busca externas, sem alterar posts e sem preencher
automaticamente vagas com links sem relacao com a pauta.
"""
import html
import re
import unicodedata
from urllib.parse import urlsplit

import requests

ALLOWED_SITES = frozenset({"https://conexotech.com.br", "https://staging.conexotech.com.br"})
_STOP = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "com",
         "para", "por", "como", "um", "uma", "em", "que", "qual", "se", "ou", "mais"}


def _tokens(s):
    if not isinstance(s, str):
        return set()
    text = unicodedata.normalize("NFKD", html.unescape(s)).lower()
    text = "".join(c for c in text if not unicodedata.combining(c))
    return {t for t in re.findall(r"[a-z0-9]+", text) if len(t) > 2 and t not in _STOP}


def selecionar_relacionados(titulo, posts, *, site="https://conexotech.com.br", limite=3):
    """Ranking auditavel de noticias publicadas, sem buscar links imaginarios."""
    if site not in ALLOWED_SITES or not 1 <= limite <= 3 or not isinstance(posts, list):
        return []
    base_host = urlsplit(site).hostname
    query = _tokens(titulo)
    seen, options = set(), []
    for post in posts[:75]:
        if not isinstance(post, dict) or post.get("status") != "publish":
            continue
        name = post.get("title")
        name = name.get("rendered", "") if isinstance(name, dict) else name
        link = post.get("link")
        if not isinstance(name, str) or not isinstance(link, str):
            continue
        try:
            u = urlsplit(link)
            if (u.scheme != "https" or u.hostname != base_host or u.username or u.password
                    or u.port not in (None, 443) or not u.path.strip("/")
                    or u.query or u.fragment):
                continue
        except ValueError:
            continue
        score = len(query & _tokens(name))
        if score == 0 or link in seen:
            continue
        seen.add(link)
        options.append((-score, len(name), name, link))
    options.sort()
    return [{"title": name, "url": link} for _, _, name, link in options[:limite]]


def buscar_relacionados_wordpress(titulo, wp_url, *, request_client=requests, limite=3, timeout=12):
    """Consulta publica de posts publicados; erro retorna [] e exige revisao."""
    target = (wp_url or "").rstrip("/")
    if target not in ALLOWED_SITES:
        return []
    try:
        response = request_client.get(
            target + "/wp-json/wp/v2/posts",
            params={"status": "publish", "per_page": 75,
                    "_fields": "id,title,link,status"},
            timeout=timeout, allow_redirects=False)
        if response.status_code != 200:
            return []
        return selecionar_relacionados(titulo, response.json(), site=target, limite=limite)
    except (requests.RequestException, ValueError, TypeError):
        return []


def anexar_relacionados(markdown, relacionados):
    """Conserva o texto original; URLs de saida validadas pelo selecionador."""
    if not isinstance(markdown, str) or not relacionados:
        return markdown
    if not isinstance(relacionados, list) or len(relacionados) > 3:
        raise ValueError("relacionados invalidos")
    output = []
    for item in relacionados:
        if not isinstance(item, dict):
            raise ValueError("relacionado invalido")
        link, name = item.get("url"), item.get("title")
        if not isinstance(link, str) or not isinstance(name, str) or not name.strip():
            raise ValueError("relacionado incompleto")
        p = urlsplit(link)
        if p.scheme != "https" or p.hostname != "conexotech.com.br" or not p.path.strip("/"):
            raise ValueError("dominio relacionado invalido")
        output.append("- [" + re.sub(r"[\[\]<>]", "", name.strip())[:130] + "](" + link + ")")
    return markdown.rstrip() + "\n\n## Leia também\n\n" + "\n".join(output) + "\n"
