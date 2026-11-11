"""Optional, private WordPress draft staging for unreviewed RSS candidates.

Never publishes, schedules, approves SEO, downloads images or bypasses a live
Editorial Gate. The independent factual review remains mandatory for publish.
"""
import hashlib
import re
import unicodedata
from urllib.parse import urlsplit, unquote

import requests

ALLOWED_SITES = frozenset(("https://conexotech.com.br", "https://staging.conexotech.com.br"))


def _slug(title, source_url):
    """Stable source-based slug; changing an AI-generated title cannot fork a post."""
    path = unquote(urlsplit(source_url).path).strip("/").split("/")[-1]
    normalized = unicodedata.normalize("NFKD", path)
    ascii_path = normalized.encode("ascii", "ignore").decode("ascii").lower()
    prefix = re.sub(r"[^a-z0-9]+", "-", ascii_path).strip("-")[:60].strip("-")
    token = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12]
    return (prefix or "pauta") + "-" + token


def _legacy_slug(title, source_url):
    """Recognize drafts created by the earlier title-based algorithm."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    prefix = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")[:60].strip("-")
    token = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12]
    return (prefix or "pauta") + "-" + token


def _matches_expected(post, title, content, allowed_slugs, featured_media_id=None,
                      excerpt=None, author_id=None):
    """Never report delivery success without version readback (edit context)."""
    if not isinstance(post, dict):
        return False
    if (type(post.get("id")) is not int or post["id"] <= 0
            or post.get("status") not in ("draft", "pending")
            or post.get("slug") not in allowed_slugs):
        return False
    body, heading = post.get("content"), post.get("title")
    if featured_media_id is not None and post.get("featured_media") != featured_media_id:
        return False
    if excerpt is not None and (not isinstance(post.get('excerpt'), dict)
                                or post['excerpt'].get('raw') != excerpt):
        return False
    if author_id is not None and post.get('author') != author_id:
        return False
    return (isinstance(body, dict) and body.get("raw") == content
            and isinstance(heading, dict) and heading.get("raw") == title.strip())


def _source_ok(url):
    if not isinstance(url, str) or not url or any(c.isspace() for c in url):
        return False
    try:
        u = urlsplit(url)
        return (u.scheme == "https" and bool(u.hostname) and "." in u.hostname
                and not u.username and not u.password and not u.fragment
                and u.port in (None, 443))
    except ValueError:
        return False


def stage_rss_draft(*, title, content, source_url, wp_url, wp_user, wp_password,
                    featured_media_id=None, media_rights_confirmed=False,
                    timeout=15, request_client=requests, excerpt=None, author_id=None):
    """Create or reuse a draft by deterministic source slug, after readback.

    On network uncertainty, never issue a second create request automatically.
    """
    target = (wp_url or "").rstrip("/")
    if (target not in ALLOWED_SITES or not wp_user or not wp_password
            or not isinstance(title, str) or len(title.strip()) < 10
            or not isinstance(content, str) or len(content.strip()) < 150
            or not _source_ok(source_url)):
        return {"acao": "bloqueado", "motivo": "entrada_rascunho_invalida", "escreveu": False}
    if ((excerpt is not None and (not isinstance(excerpt, str) or not excerpt.strip()))
            or (author_id is not None and (type(author_id) is not int or author_id <= 0))):
        return {"acao": "bloqueado", "motivo": "metadados_rascunho_invalidos", "escreveu": False}
    if featured_media_id is not None:
        if (type(featured_media_id) is not int or featured_media_id <= 0
                or media_rights_confirmed is not True):
            return {"acao": "bloqueado", "motivo": "imagem_sem_direitos_ou_id",
                    "escreveu": False}
    elif media_rights_confirmed is True:
        return {"acao": "bloqueado", "motivo": "imagem_id_ausente", "escreveu": False}
    slug = _slug(title, source_url)
    endpoint = target + "/wp-json/wp/v2/posts"
    auth = (wp_user, wp_password)
    try:
        if featured_media_id is not None:
            # Reuse only media that already exists inside the authenticated WP
            # library; license confirmation must come from the human operator.
            media = request_client.get(
                target + "/wp-json/wp/v2/media/" + str(featured_media_id),
                params={"context": "edit", "_fields": "id,media_type,mime_type,alt_text"},
                auth=auth, timeout=timeout, allow_redirects=False)
            data = media.json() if media.status_code == 200 else {}
            if (not isinstance(data, dict) or data.get("id") != featured_media_id
                    or data.get("media_type") != "image"
                    or data.get("mime_type") not in ("image/jpeg", "image/png", "image/webp")
                    or not isinstance(data.get("alt_text"), str)
                    or not data["alt_text"].strip()):
                return {"acao": "bloqueado", "motivo": "midia_wp_nao_validada",
                        "escreveu": False, "retry_automatic": False}
        # Search by stable slug first, then by the previous title-based slug
        # for backward compatibility. An existing post is never overwritten.
        matches = []
        for candidate in dict.fromkeys((slug, _legacy_slug(title, source_url))):
            existing = request_client.get(
                endpoint, params={"slug": candidate, "context": "edit",
                                   "status": ["draft", "pending", "publish", "future", "private"]},
                auth=auth, timeout=timeout, allow_redirects=False)
            if existing.status_code != 200:
                return {"acao": "falha", "motivo": "consulta_wp_indisponivel", "escreveu": False,
                        "retry_automatic": False}
            found = existing.json()
            if not isinstance(found, list):
                return {"acao": "falha", "motivo": "consulta_wp_invalida", "escreveu": False,
                        "retry_automatic": False}
            matches.extend(found)
        ids = {x.get("id") for x in matches if isinstance(x, dict)}
        if matches:
            if len(ids) != 1 or not all(isinstance(x, dict) for x in matches):
                return {"acao": "bloqueado", "motivo": "slug_ja_ocupado", "escreveu": False,
                        "retry_automatic": False}
            post_id = next(iter(ids))
            if type(post_id) is not int or post_id <= 0:
                return {"acao": "bloqueado", "motivo": "resposta_wp_invalida", "escreveu": False,
                        "retry_automatic": False}
            verified = request_client.get(endpoint + "/" + str(post_id),
                                          params={"context": "edit"}, auth=auth,
                                          timeout=timeout, allow_redirects=False)
            current = verified.json() if verified.status_code == 200 else {}
            if not _matches_expected(current, title, content, {slug, _legacy_slug(title, source_url)},
                                     featured_media_id, excerpt, author_id):
                return {"acao": "bloqueado", "motivo": "versao_rascunho_divergente",
                        "post_id": post_id, "escreveu": False, "retry_automatic": False}
            return {"acao": "publicado_rascunho", "post_id": post_id,
                    "status": current["status"], "wp_link": current.get("link"),
                    "escreveu": False, "reutilizado": True, "revisao_factual": "PENDENTE"}
        payload = {"title": title.strip(), "content": content, "slug": slug,
                   "status": "draft", "comment_status": "closed"}
        if featured_media_id is not None:
            payload["featured_media"] = featured_media_id
        if excerpt is not None:
            payload['excerpt'] = excerpt
        if author_id is not None:
            payload['author'] = author_id
        result = request_client.post(endpoint, json=payload,
                                     auth=auth, timeout=timeout, allow_redirects=False)
        if result.status_code != 201:
            return {"acao": "falha", "motivo": "wp_recusou_rascunho",
                    "http_status": result.status_code, "escreveu": False}
        post = result.json()
        post_id = post.get("id") if isinstance(post, dict) else None
        if type(post_id) is not int or post_id <= 0 or post.get("status") != "draft":
            return {"acao": "falha", "motivo": "resposta_wp_invalida_inspecionar",
                    "escreveu": False, "escrita_indeterminada": True,
                    "retry_automatic": False}
        verified = request_client.get(endpoint + "/" + str(post_id),
                                      params={"context": "edit"}, auth=auth,
                                      timeout=timeout, allow_redirects=False)
        readback = verified.json() if verified.status_code == 200 else {}
        if (not _matches_expected(readback, title, content, {slug}, featured_media_id, excerpt, author_id)
                or readback.get("status") != "draft"):
            return {"acao": "falha", "motivo": "readback_wp_divergente_inspecionar",
                    "post_id": post_id, "escreveu": True, "retry_automatic": False}
        return {"acao": "publicado_rascunho", "post_id": post_id, "status": "draft",
                "wp_link": readback.get("link"), "escreveu": True,
                "revisao_factual": "PENDENTE", "retry_automatic": False}
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return {"acao": "falha", "motivo": "transporte_indeterminado_inspecionar_slug",
                "slug": slug, "escreveu": False, "retry_automatic": False}
