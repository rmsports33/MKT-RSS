"""MKTFLOW.wp_publisher — publicação WP clássica (v3.11 congelada).
WPConfig + gate (_check_gate): só PASS publica; demais forçam draft."""
import base64
import logging

import requests

logger = logging.getLogger("mktflow.wp")


class WPConfig:
    def __init__(self, url: str = "", user: str = "", app_password: str = "", timeout: int = 10):
        self.url = (url or "").rstrip("/")
        self.user = user or ""
        self.app_password = app_password or ""
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.url and self.user and self.app_password)

    def auth_header(self) -> str:
        token = base64.b64encode(f"{self.user}:{self.app_password}".encode()).decode()
        return f"Basic {token}"


def _check_gate(status_validacao: str, status_desejado: str = "draft") -> str:
    """Retorna status final: publish só com PASS; resto vira draft."""
    if (status_desejado or "draft").lower() == "publish" and status_validacao == "PASS":
        return "publish"
    return "draft"


def publicar_no_wordpress(cfg: WPConfig, titulo: str, conteudo_html: str,
                          status_validacao: str, status_desejado: str = "draft",
                          categoria_ids=None, tag_ids=None) -> dict:
    if not isinstance(cfg, WPConfig) or not cfg.is_configured():
        return {"erro": "WPConfig incompleto — preencha url/user/app_password"}
    final = _check_gate(status_validacao, status_desejado)
    if (status_desejado or "").lower() == "publish" and final != "publish":
        return {"erro": f"Publicação bloqueada: status_validacao={status_validacao} — só PASS permite publish.",
                "status_validacao": status_validacao}
    payload = {"title": titulo, "content": conteudo_html, "status": final}
    if categoria_ids:
        payload["categories"] = categoria_ids
    if tag_ids:
        payload["tags"] = tag_ids
    try:
        r = requests.post(f"{cfg.url}/wp-json/wp/v2/posts",
                          headers={"Authorization": cfg.auth_header(), "Content-Type": "application/json",
                                   "User-Agent": "MKT-Flow/3.0"},
                          json=payload, timeout=cfg.timeout)
        if r.status_code in (200, 201):
            d = r.json()
            return {"post_id": d.get("id"), "link": d.get("link"), "status": d.get("status"),
                    "status_validacao": status_validacao}
        return {"erro": f"WP {r.status_code}: {r.text[:200]}"}
    except requests.Timeout:
        return {"erro": f"WP timeout após {cfg.timeout}s"}
    except Exception as e:
        return {"erro": f"Falha WP: {str(e)[:150]}"}
