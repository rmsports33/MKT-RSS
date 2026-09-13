"""
mkt_flow_p0.wp_publisher — Publicação WordPress via REST API
Gateado por status_validacao==PASS para publish; draft sempre permitido.
"""
import base64
import logging
import requests

logger = logging.getLogger("wp_publisher")

def _auth_header(user: str, app_password: str) -> str:
    token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return f"Basic {token}"


def _get_ou_criar_termo(wp_url: str, user: str, app_password: str, tipo: str, nome: str, timeout: int = 10):
    """Busca categoria/tag por nome; cria se não existir. Retorna id ou None.

    tipo: "categories" | "tags". Falha de rede → None (publica sem taxonomia).
    """
    nome = (nome or "").strip()
    if not nome:
        return None
    base = f"{wp_url}/wp-json/wp/v2/{tipo}"
    headers = {"Authorization": _auth_header(user, app_password), "User-Agent": "MKT-Flow-P0/3.6"}
    try:
        r = requests.get(base, headers=headers, params={"search": nome, "per_page": 5}, timeout=timeout)
        if r.status_code == 200:
            for item in r.json():
                if str(item.get("name", "")).lower() == nome.lower():
                    return item.get("id")
        r = requests.post(base, headers={**headers, "Content-Type": "application/json"},
                          json={"name": nome}, timeout=timeout)
        if r.status_code in (200, 201):
            return r.json().get("id")
    except Exception as e:
        logger.warning(f"WP {tipo} '{nome}' falhou: {e}")
    return None


def garantir_categoria(wp_url: str, user: str, app_password: str, nome: str, timeout: int = 10):
    return _get_ou_criar_termo((wp_url or "").rstrip("/"), user, app_password, "categories", nome, timeout)


def garantir_tag(wp_url: str, user: str, app_password: str, nome: str, timeout: int = 10):
    return _get_ou_criar_termo((wp_url or "").rstrip("/"), user, app_password, "tags", nome, timeout)


def _aplicar_rank_math(wp_url: str, user: str, app_password: str, post_id, rank_math: dict, timeout: int = 10) -> dict:
    """2º passo: grava title/description/focus no Rank Math. Falha → só aviso (post já existe)."""
    meta = {}
    if rank_math.get("title"):
        meta["rank_math_title"] = str(rank_math["title"])[:60]
    if rank_math.get("description"):
        meta["rank_math_description"] = str(rank_math["description"])[:160]
    if rank_math.get("focus"):
        meta["rank_math_focusKeyword"] = str(rank_math["focus"])
    if not meta:
        return {}
    try:
        r = requests.post(f"{wp_url}/wp-json/wp/v2/posts/{post_id}",
                          headers={"Authorization": _auth_header(user, app_password),
                                   "Content-Type": "application/json", "User-Agent": "MKT-Flow-P0/3.6"},
                          json={"meta": meta}, timeout=timeout)
        if r.status_code in (200, 201):
            return {"meta_ok": True}
        return {"meta_aviso": f"Rank Math recusou ({r.status_code}) — meta vai só no HTML"}
    except Exception as e:
        return {"meta_aviso": f"Rank Math falhou: {str(e)[:100]} — meta vai só no HTML"}


def publicar_no_wordpress(
    titulo: str,
    conteudo_html: str,
    status_validacao: str,
    wp_url: str,
    wp_user: str,
    wp_app_password: str,
    status_desejado: str = "draft",
    categoria_ids=None,
    tag_ids=None,
    imagem_url: str = "",
    timeout: int = 10,
    slug: str = "",
    rank_math: dict = None,
) -> dict:
    """
    Publica no WP. status_desejado: draft | publish
    Se status_validacao != PASS e status_desejado == publish -> BLOQUEIA e força draft.
    slug vai no campo slug; rank_math={title,description,focus} em 2º passo
    (falha do meta nunca apaga o post — vira aviso).
    Retorna {"post_id":..., "link":..., "status":"draft|publish"} ou {"erro":...}
    """
    wp_url = (wp_url or "").rstrip("/")
    if not wp_url or not wp_user or not wp_app_password:
        return {"erro": "WP_URL/WP_USER/WP_APP_PASSWORD ausentes no .env"}

    # Gate de compliance
    status_desejado = (status_desejado or "draft").lower()
    if status_desejado == "publish" and status_validacao != "PASS":
        return {
            "erro": f"Publicação bloqueada: status_validacao={status_validacao} — só PASS permite publish. Use draft.",
            "status_validacao": status_validacao,
        }

    # Se UNKNOWN/FAIL mas pediram publish, força draft
    status_final = "publish" if (status_desejado == "publish" and status_validacao == "PASS") else "draft"

    headers = {
        "Authorization": _auth_header(wp_user, wp_app_password),
        "Content-Type": "application/json",
        "User-Agent": "MKT-Flow-P0/3.6",
    }

    # Upload de imagem destacada se houver
    featured_media = None
    if imagem_url and imagem_url.startswith("http"):
        try:
            img_resp = requests.get(imagem_url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            img_resp.raise_for_status()
            # WP media endpoint
            media_headers = {
                "Authorization": _auth_header(wp_user, wp_app_password),
                "Content-Disposition": 'attachment; filename="featured.jpg"',
                "Content-Type": img_resp.headers.get("Content-Type", "image/jpeg"),
            }
            media_resp = requests.post(
                f"{wp_url}/wp-json/wp/v2/media",
                headers=media_headers,
                data=img_resp.content,
                timeout=timeout,
            )
            if media_resp.status_code in (200, 201):
                featured_media = media_resp.json().get("id")
            else:
                logger.warning(f"WP media falhou {media_resp.status_code}: {media_resp.text[:200]}")
        except Exception as e:
            logger.warning(f"WP imagem falhou: {e}")

    payload = {
        "title": titulo,
        "content": conteudo_html,
        "status": status_final,
    }
    if categoria_ids:
        payload["categories"] = categoria_ids
    if tag_ids:
        payload["tags"] = tag_ids
    if featured_media:
        payload["featured_media"] = featured_media
    if slug:
        payload["slug"] = slug

    try:
        resp = requests.post(
            f"{wp_url}/wp-json/wp/v2/posts",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            out = {
                "post_id": data.get("id"),
                "link": data.get("link"),
                "status": data.get("status"),
                "status_validacao": status_validacao,
            }
            if rank_math:
                out.update(_aplicar_rank_math(wp_url, wp_user, wp_app_password,
                                              data.get("id"), rank_math, timeout))
            return out
        return {"erro": f"WP {resp.status_code}: {resp.text[:300]}"}
    except requests.Timeout:
        return {"erro": f"WP timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha WP: {str(e)[:200]}"}
