"""Único transporte editorial: gate canônico fixado por hash + escrita assinada.

Chave no executor confiável, nunca no pacote. Sem fallback ao REST/MCP direto.
"""
import base64
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import requests

SITE = "https://conexotech.com.br"


def load_core(root):
    root = Path(root).resolve()
    lock = json.loads(Path(__file__).with_name("editorial_core.lock.json").read_text())
    for name, wanted in lock["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != wanted:
            raise ValueError("núcleo ausente/alterado: " + name)
    spec = importlib.util.spec_from_file_location("_conexo_trusted_write", root / "scripts/editorial_write.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def publish_package(package, *, core_root, wp_url, wp_user, wp_password,
                    actor_id, intent="stage", publication_reference=None,
                    timeout=15, operation_nonce=None):
    """Não gera texto nem atesta fatos. Encaminha versão realmente revisada.

    Prévia stage permanece draft e não conta como entrega. Timeout nunca
    cria outra operação automaticamente; conservar nonce e inspecionar remoto.
    """
    nonce = operation_nonce
    try:
        if not isinstance(wp_url, str) or wp_url.rstrip("/") != SITE or not wp_user or not wp_password:
            raise ValueError("site/credenciais inválidos")
        if intent not in {"stage", "draft", "publish", "schedule"} or type(actor_id) is not int or actor_id <= 0:
            raise ValueError("intenção/ator inválidos")
        core = load_core(core_root)
        v = core.validator()
        errors, blockers = v.evaluate(package, Path(core_root), for_staging=intent == "stage")
        if intent in {"stage", "draft"}:
            blockers = [b for b in blockers if b != v.HUMAN_PENDING]
        if errors or blockers:
            raise ValueError("gate editorial bloqueou: " + "; ".join(errors + blockers))
        secret = os.environ.get("CONEXO_EDITORIAL_GATE_KEY", "").encode()
        if len(secret) < 32:
            raise ValueError("chave do executor ausente")
        wp = package["payload"]["wordpress"]
        post_id = wp["post_id"]
        auth = (wp_user, wp_password)
        if nonce is not None:
            if not isinstance(nonce, str) or not re.fullmatch(r"[a-f0-9]{32}", nonce):
                raise ValueError("identidade de retomada inválida")
            operation = requests.get(f"{SITE}/wp-json/conexo/v1/editorial/operation/{nonce}",
                auth=auth, timeout=timeout, allow_redirects=False)
            if operation.status_code != 200 or operation.json().get("state") != "COMPLETE":
                raise ValueError("operação não confirmada; inspecionar antes de nova escrita")
            result = operation.json()["result"]
            if result.get("version_sha256") != package["version_sha256"] or result.get("intent") != intent or result.get("nonce") != nonce:
                raise ValueError("retomada de outra versão/intenção")
            if type(result.get("post_id")) is not int or result["post_id"] <= 0 or (post_id and result["post_id"] != post_id):
                raise ValueError("retomada de outro artigo")
            read = requests.get(f"{SITE}/wp-json/conexo/v1/editorial/snapshot/{result['post_id']}",
                auth=auth, timeout=timeout, allow_redirects=False)
            if read.status_code != 200 or read.json().get("snapshot") != result.get("snapshot"):
                raise ValueError("versão remota diverge da operação retomada")
            result.update(acao="staged_for_theme_review" if intent == "stage" else "written_and_verified",
                editorial_delivered=intent != "stage", retry_automatic=False, resumed=True)
            return result
        snapshot, link = None, None
        if post_id:
            response = requests.get(f"{SITE}/wp-json/conexo/v1/editorial/snapshot/{post_id}",
                                    auth=auth, timeout=timeout, allow_redirects=False)
            if response.status_code != 200:
                raise ValueError("snapshot autenticado indisponível")
            remote = response.json()
            snapshot, link = remote["snapshot"], remote["link"]
        if intent in {"publish", "schedule"} and package["payload"]["substantive_review"]["article_format"] == "noticia":
            from editorial_wordpress_readiness import require_wordpress_readiness
            require_wordpress_readiness({"id": snapshot["ID"], "title": snapshot["post_title"],
                "content": snapshot["post_content"], "slug": snapshot["post_name"],
                "status": snapshot["post_status"], "categories": snapshot["post_category"],
                "featured_media": snapshot["meta_input"]["_thumbnail_id"], "link": link},
                expected_category_id=wp.get("news_category_id", 10))
        envelope = core.prepare_write(package, core_root, intent=intent, actor_id=actor_id,
            key=secret, snapshot=snapshot, publication_reference=publication_reference, nonce=nonce)
        claim = json.loads(base64.urlsafe_b64decode(envelope["receipt"] + "=" * (-len(envelope["receipt"]) % 4)))
        nonce = claim["nonce"]
        response = requests.post(f"{SITE}/wp-json/conexo/v1/editorial/write", json=envelope,
                                 auth=auth, timeout=timeout, allow_redirects=False)
        if response.status_code not in (200, 201):
            return {"erro": "servidor recusou a operação editorial", "http_status": response.status_code,
                    "nonce": nonce, "retry_automatic": False}
        result = response.json()
        if result.get("nonce") != nonce or result.get("version_sha256") != package["version_sha256"] or type(result.get("post_id")) is not int or result["post_id"] <= 0:
            raise ValueError("identidade do readback divergente")
        expected = claim["post"].copy()
        expected["ID"] = result["post_id"]
        if intent != "schedule":
            expected["post_date_gmt"] = result.get("snapshot", {}).get("post_date_gmt")
        if not isinstance(expected["post_date_gmt"], str):
            raise ValueError("data do readback ausente")
        expected["post_category"] = sorted(expected["post_category"])
        if result.get("snapshot") != expected or result.get("status") != expected["post_status"]:
            raise ValueError("readback divergente")
        # Confere novamente, inclusive em repetição idempotente de recibo antigo.
        read = requests.get(f"{SITE}/wp-json/conexo/v1/editorial/snapshot/{result['post_id']}",
                            auth=auth, timeout=timeout, allow_redirects=False)
        if read.status_code != 200 or read.json().get("snapshot") != expected:
            raise ValueError("versão atual remota diverge da operação")
        result.update(acao="staged_for_theme_review" if intent == "stage" else "written_and_verified",
                      editorial_delivered=intent != "stage", retry_automatic=False)
        return result
    except (ValueError, TypeError, KeyError, OSError, requests.RequestException) as exc:
        # Não ecoar exceção de transporte que possa conter URL/credencial.
        return {"erro": "fluxo editorial bloqueado", "reason": str(exc) if not isinstance(exc, requests.RequestException) else "erro de transporte; inspecionar nonce antes de repetir",
                "nonce": nonce, "retry_automatic": False}
