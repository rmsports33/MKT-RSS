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
) -> dict:
    """
    Publica no WP. status_desejado: draft | publish
    Se status_validacao != PASS e status_desejado == publish -> BLOQUEIA e força draft.
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

    try:
        resp = requests.post(
            f"{wp_url}/wp-json/wp/v2/posts",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            return {
                "post_id": data.get("id"),
                "link": data.get("link"),
                "status": data.get("status"),
                "status_validacao": status_validacao,
            }
        return {"erro": f"WP {resp.status_code}: {resp.text[:300]}"}
    except requests.Timeout:
        return {"erro": f"WP timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha WP: {str(e)[:200]}"}
