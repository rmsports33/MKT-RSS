"""Único transporte editorial: gate canônico fixado por hash + escrita assinada.

Chave no executor confiável, nunca no pacote. Sem fallback ao REST/MCP direto.
"""
import base64
import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
from pathlib import Path
import requests

SITE = "https://conexotech.com.br"


def _effective_seo_key():
    """Optional single-master-key mode. Existing dedicated SEO secrets win."""
    explicit = os.environ.get("CONEXO_NATIVE_SEO_SIGNING_KEY", "")
    if explicit:
        key = explicit.encode("utf-8")
        return key if len(key) >= 32 else b""
    if os.environ.get("CONEXO_DERIVE_SEO_KEY_FROM_EDITORIAL") != "1":
        return b""
    master = os.environ.get("CONEXO_EDITORIAL_GATE_KEY", "").encode("utf-8")
    if len(master) < 32:
        return b""
    return hmac.new(master, b"conexo-native-seo-v1", hashlib.sha256).digest()


def _seo_key_mode():
    explicit = os.environ.get("CONEXO_NATIVE_SEO_SIGNING_KEY", "")
    if explicit:
        return "explicit" if len(explicit.encode("utf-8")) >= 32 else "invalid"
    if os.environ.get("CONEXO_DERIVE_SEO_KEY_FROM_EDITORIAL") == "1":
        return "derived" if len(os.environ.get("CONEXO_EDITORIAL_GATE_KEY", "").encode("utf-8")) >= 32 else "invalid"
    return "absent"


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


def _finalize_seo_after_publish(package, result, *, envelope, wp_auth, timeout):
    """Only after signed editorial readback. Missing key stays pending, not an error
    that could encourage blindly repeating a publication POST.
    """
    key = _effective_seo_key()
    if len(key) < 32:
        return {"status": "pending_signing_key"}
    from mkt_flow_p0.seo_delivery_signing import prepare_signed_seo_contract
    try:
        contract = prepare_signed_seo_contract(package, result, seo_key=key)
    except (ValueError, TypeError, KeyError):
        return {"status": "blocked_contract_review"}
    try:
        response = requests.post(
            f"{SITE}/wp-json/conexo/v1/editorial/seo-finalize",
            json={"nonce": result["nonce"],
                  "publication_signature": envelope["signature"],
                  "contract": contract},
            auth=wp_auth, timeout=timeout, allow_redirects=False,
        )
        if response.status_code != 200:
            return {"status": "remote_refused_inspect", "http_status": response.status_code,
                    "retry_automatic": False}
        body = response.json()
        if (not isinstance(body, dict) or body.get("post_id") != result["post_id"]
                or body.get("status") != "verified"):
            return {"status": "readback_mismatch_inspect", "retry_automatic": False}
        return {"status": "verified", "idempotent": body.get("idempotent") is True}
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return {"status": "transport_unknown_inspect", "retry_automatic": False}


def publish_package(package, *, core_root, wp_url, wp_user, wp_password,
                    actor_id, intent="stage", publication_reference=None,
                    timeout=15, operation_nonce=None, seo_publication_signature=None,
                    trace_run_id=None):
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
        # Explicit server-side broker mode, never an automatic fallback.
        # HMAC stays inside WP Vault; Turso trace/readback and the same
        # canonical independent quality+approval Gate remain mandatory.
        mode = os.environ.get("CONEXO_EDITORIAL_TRANSPORT", "")
        if mode not in ("", "signed", "wp_broker"):
            raise ValueError("transporte editorial nao homologado")
        # Require substantive editorial evidence on both signed and broker paths.
        # No caller-provided assessment can replace trusted Turso approval.
        if intent in {"publish", "schedule"}:
            from mkt_flow_p0.editorial_substance import assess_editorial_package
            editorial = package.get("editorial_assessment") if isinstance(package, dict) else None
            if not isinstance(editorial, dict):
                raise ValueError("avaliação editorial obrigatória ausente")
            assessment = assess_editorial_package(
                package, editorial.get("brief"), editorial.get("review"),
                editorial.get("receipts"))
            if assessment["status"] != "REQUIRES_AUTHENTICATED_GATE":
                raise ValueError("avaliação substantiva pendente: " + "; ".join(assessment["blockers"]))
        if mode == "wp_broker" and intent in {"publish", "schedule"}:
            if operation_nonce is not None:
                raise ValueError("broker exige reconciliacao remota; retomada nao pode repetir escrita")
            if not isinstance(package, dict) or not isinstance(package.get("payload"), dict):
                raise ValueError("pacote editorial ausente")
            from mkt_flow_p0.editorial_broker_transport import publish_via_broker
            return publish_via_broker(
                package, core_root=core_root, wp_url=wp_url,
                wp_user=wp_user, wp_password=wp_password,
                trace_run_id=trace_run_id, intent=intent,
                publication_reference=publication_reference,
                post_date_gmt=package.get("payload", {}).get("wordpress", {}).get("post_date_gmt")
                    if intent == "schedule" else None,
                timeout=timeout,
                require_signed_seo=intent == "publish" and os.environ.get("CONEXO_REQUIRE_SIGNED_SEO") == "1",
            )
        core = load_core(core_root)
        v = core.validator()
        errors, blockers = v.evaluate(package, Path(core_root), for_staging=intent == "stage")
        if intent in {"stage", "draft"}:
            blockers = [b for b in blockers if b != v.HUMAN_PENDING]
        if errors or blockers:
            raise ValueError("gate editorial bloqueou: " + "; ".join(errors + blockers))
        # Mandatory trusted provenance preflight for publish/schedule.
        # Private stage/draft remain unaffected. The WordPress broker
        # performs the same check independently before any write.
        if intent in ("publish", "schedule"):
            from mkt_flow_p0.editorial_trace_gate import require_release_trace
            require_release_trace(package, trace_run_id)
        # Strict mode becomes mandatory only after the executor and SEO Gate
        # have been provisioned. Check before any publication-side network call.
        if intent == "publish" and os.environ.get("CONEXO_REQUIRE_SIGNED_SEO") == "1":
            payload = package.get("payload", {})
            seo = payload.get("seo")
            seo_key = _effective_seo_key()
            slug = payload.get("slug")
            if (not isinstance(seo, dict)
                    or seo.get("provider") != "native"
                    or not isinstance(slug, str)
                    or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
                    or seo.get("canonical") != f"{SITE}/{slug}/"
                    or not isinstance(seo.get("title"), str)
                    or not seo["title"].strip()
                    or len(seo["title"].strip().encode("utf-8")) > 250
                    or not isinstance(seo.get("description"), str)
                    or not seo["description"].strip()
                    or len(seo["description"].strip().encode("utf-8")) > 600
                    or len(seo_key) < 32):
                raise ValueError("SEO aprovado/chave privada ausentes; publicacao bloqueada")
        secret = os.environ.get("CONEXO_EDITORIAL_GATE_KEY", "").encode()
        if len(secret) < 32:
            raise ValueError("chave do executor ausente")
        wp = package["payload"]["wordpress"]
        post_id = wp["post_id"]
        auth = (wp_user, wp_password)
        if intent == "publish" and os.environ.get("CONEXO_REQUIRE_SIGNED_SEO") == "1":
            # Guarded GET is a preflight, not proof of successful SEO delivery.
            # Refuse to publish when the Gate or its server-side SEO key
            # is unavailable; never let a later failed SEO step go unnoticed.
            challenge = secrets.token_hex(16)
            readiness = requests.get(
                f"{SITE}/wp-json/conexo/v1/editorial/seo-readiness",
                params={"challenge": challenge},
                auth=auth, timeout=timeout, allow_redirects=False)
            if readiness.status_code != 200:
                raise ValueError("Gate de SEO assinado indisponivel")
            state = readiness.json()
            if (not isinstance(state, dict)
                    or state.get("schema") != "conexo-seo-readiness/1"
                    or state.get("editorial_gate_ready") is not True
                    or state.get("seo_signing_ready") is not True
                    or state.get("seo_public_output_ready") is not True
                    or state.get("seo_key_mode") != _seo_key_mode()
                    or not isinstance(state.get("seo_key_proof"), str)
                    or not hmac.compare_digest(
                        state["seo_key_proof"],
                        hmac.new(_effective_seo_key(),
                                 ("conexo-seo-readiness-v1:" + challenge).encode(),
                                 hashlib.sha256).hexdigest())):
                raise ValueError("Gate/chave de SEO no WordPress nao prontos")
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
            if intent == "publish":
                # Never regenerate an original editorial receipt on resume.
                # The already-signed envelope must be retained by the trusted executor.
                if (isinstance(seo_publication_signature, str)
                        and re.fullmatch(r"[a-f0-9]{64}", seo_publication_signature)):
                    result["seo_private_delivery"] = _finalize_seo_after_publish(
                        package, result,
                        envelope={"signature": seo_publication_signature},
                        wp_auth=auth, timeout=timeout)
                else:
                    result["seo_private_delivery"] = {
                        "status": "pending_original_publication_signature",
                        "retry_automatic": False,
                    }
                result["publicacao_seo_concluidos"] = result["seo_private_delivery"].get("status") == "verified"
                if not result["publicacao_seo_concluidos"]:
                    result["acao"] = "published_seo_pending_inspection"
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
        if intent == "publish":
            result["seo_private_delivery"] = _finalize_seo_after_publish(
                package, result, envelope=envelope, wp_auth=auth, timeout=timeout)
            result["publicacao_seo_concluidos"] = result["seo_private_delivery"].get("status") == "verified"
            if not result["publicacao_seo_concluidos"]:
                result["acao"] = "published_seo_pending_inspection"
        return result
    except (ValueError, TypeError, KeyError, OSError, requests.RequestException) as exc:
        # Não ecoar exceção de transporte que possa conter URL/credencial.
        return {"erro": "fluxo editorial bloqueado", "reason": str(exc) if not isinstance(exc, requests.RequestException) else "erro de transporte; inspecionar nonce antes de repetir",
                "nonce": nonce, "retry_automatic": False}
