"""Optional, private WordPress draft staging for unreviewed RSS candidates.

Never publishes, schedules, approves SEO, uploads images or bypasses a live
Editorial Gate. The independent factual review remains mandatory for publish.
"""
import hashlib
import re
import unicodedata
from urllib.parse import urlsplit

import requests

ALLOWED_SITES = frozenset(("https://conexotech.com.br", "https://staging.conexotech.com.br"))


def _slug(title, source_url):
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    prefix = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")[:60].strip("-")
    token = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:12]
    return (prefix or "pauta") + "-" + token


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
                    timeout=15, request_client=requests):
    """Create or reuse a draft by deterministic source slug, after readback.

    On network uncertainty, never issue a second create request automatically.
    """
    target = (wp_url or "").rstrip("/")
    if (target not in ALLOWED_SITES or not wp_user or not wp_password
            or not isinstance(title, str) or len(title.strip()) < 10
            or not isinstance(content, str) or len(content.strip()) < 150
            or not _source_ok(source_url)):
        return {"acao": "bloqueado", "motivo": "entrada_rascunho_invalida", "escreveu": False}
    slug = _slug(title, source_url)
    endpoint = target + "/wp-json/wp/v2/posts"
    auth = (wp_user, wp_password)
    try:
        existing = request_client.get(endpoint, params={"slug": slug, "context": "edit"},
                                      auth=auth, timeout=timeout, allow_redirects=False)
        if existing.status_code != 200:
            return {"acao": "falha", "motivo": "consulta_wp_indisponivel", "escreveu": False}
        matches = existing.json()
        if not isinstance(matches, list):
            return {"acao": "falha", "motivo": "consulta_wp_invalida", "escreveu": False}
        if matches:
            if len(matches) != 1 or matches[0].get("status") not in ("draft", "pending"):
                return {"acao": "bloqueado", "motivo": "slug_ja_ocupado", "escreveu": False}
            return {"acao": "publicado_rascunho", "post_id": matches[0]["id"],
                    "status": matches[0]["status"], "wp_link": matches[0].get("link"),
                    "escreveu": False, "reutilizado": True, "revisao_factual": "PENDENTE"}
        result = request_client.post(endpoint, json={
            "title": title.strip(), "content": content, "slug": slug,
            "status": "draft", "comment_status": "closed",
        }, auth=auth, timeout=timeout, allow_redirects=False)
        if result.status_code != 201:
            return {"acao": "falha", "motivo": "wp_recusou_rascunho",
                    "http_status": result.status_code, "escreveu": False}
        post = result.json()
        post_id = post.get("id") if isinstance(post, dict) else None
        if type(post_id) is not int or post_id <= 0 or post.get("status") != "draft":
            return {"acao": "falha", "motivo": "resposta_wp_invalida_inspecionar",
                    "escreveu": False, "retry_automatic": False}
        verified = request_client.get(endpoint + "/" + str(post_id),
                                      params={"context": "edit"}, auth=auth,
                                      timeout=timeout, allow_redirects=False)
        readback = verified.json() if verified.status_code == 200 else {}
        if (not isinstance(readback, dict) or readback.get("status") != "draft"
                or readback.get("slug") != slug):
            return {"acao": "falha", "motivo": "readback_wp_divergente_inspecionar",
                    "post_id": post_id, "escreveu": True, "retry_automatic": False}
        return {"acao": "publicado_rascunho", "post_id": post_id, "status": "draft",
                "wp_link": readback.get("link"), "escreveu": True,
                "revisao_factual": "PENDENTE", "retry_automatic": False}
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return {"acao": "falha", "motivo": "transporte_indeterminado_inspecionar_slug",
                "slug": slug, "escreveu": False, "retry_automatic": False}
