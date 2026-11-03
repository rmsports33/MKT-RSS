"""Assina contrato SEO somente após readback do publicador editorial confiável.

NÃO faz requisições HTTP, NÃO grava metadados WordPress e NÃO libera o
contrato sem uma publicação já verificada. O transporte futuro deve acoplar a
escrita privada à mesma autorização editorial, nunca expor esta chave via REST.
"""
import hashlib
import hmac
import json
import re
from urllib.parse import urlsplit

SITE = "https://conexotech.com.br"

def prepare_signed_seo_contract(package, verified_result, *, seo_key):
    """Constrói envelope privado após retorno do transport editorial autenticado.

    A chamada é restrita ao processo que acabou de validar readback contra
    o recibo do Gate. Dados controlados pelo usuário isoladamente não comprovam
    autorização: este módulo não oferece endpoint e não executa gravação.
    """
    if not isinstance(package, dict) or package.get("stage") != "ready":
        raise ValueError("pacote editorial nao aprovado")
    if not isinstance(verified_result, dict):
        raise ValueError("readback editorial ausente")
    if (verified_result.get("intent") != "publish"
            or verified_result.get("status") != "publish"
            or verified_result.get("editorial_delivered") is not True
            or verified_result.get("retry_automatic") is not False
            or verified_result.get("version_sha256") != package.get("version_sha256")):
        raise ValueError("recibo de publicacao nao confirmado")
    key = seo_key.encode("utf-8") if isinstance(seo_key, str) else seo_key
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("chave privada SEO ausente")
    payload = package.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("payload editorial ausente")
    seo = payload.get("seo")
    if not isinstance(seo, dict):
        raise ValueError("seo revisado nao incluído no pacote")
    post = verified_result.get("snapshot")
    post_id = verified_result.get("post_id")
    if not isinstance(post, dict) or type(post_id) is not int or post_id <= 0:
        raise ValueError("snapshot WordPress invalido")
    if (post.get("ID") != post_id or post.get("post_type") != "post"
            or post.get("post_status") != "publish"
            or post.get("post_content") != payload.get("content")
            or post.get("post_title") != payload.get("title")
            or post.get("post_name") != payload.get("slug")):
        raise ValueError("snapshot nao corresponde ao pacote aprovado")
    canonical = verified_result.get("link")
    parsed = urlsplit(canonical) if isinstance(canonical, str) else None
    if (not parsed or parsed.scheme != "https" or parsed.netloc != "conexotech.com.br"
            or parsed.path != "/" + post["post_name"] + "/"
            or parsed.query or parsed.fragment):
        raise ValueError("canonical remota divergente")
    title, description = seo.get("title"), seo.get("description")
    if (not isinstance(title, str) or not title.strip()
            or len(title.strip().encode("utf-8")) > 250
            or not isinstance(description, str) or not description.strip()
            or len(description.strip().encode("utf-8")) > 600):
        raise ValueError("metadados SEO do pacote invalidos")
    title, description = title.strip(), description.strip()
    digest = hashlib.sha256(post["post_content"].encode("utf-8")).hexdigest()
    message = {
        "domain": "conexo-seo-v1",
        "post_id": post_id,
        "canonical": canonical,
        "title": title,
        "description": description,
        "content_sha256": digest,
    }
    encoded = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": "1.0",
        "provider": "native",
        "content_post_id": post_id,
        "canonical": canonical,
        "title": title,
        "description": description,
        "approved_for_publication": True,
        "delivery_status": "approved",
        "content_sha256": digest,
        "signature": hmac.new(key, encoded, hashlib.sha256).hexdigest(),
    }
