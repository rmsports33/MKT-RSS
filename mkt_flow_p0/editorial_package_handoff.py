"""Vincula SEO consultivo ao pacote canônico *antes* de revisão e aceite.

Sem WordPress ou rede. O handoff jamais transforma 'staging' em aprovação.
O núcleo Conexo OS deve validar novamente o pacote e produzir novo recibo.
"""
from copy import deepcopy
import hashlib
import json
import re

SITE = "https://conexotech.com.br"

def _digest(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

def vincular_seo_antes_da_revisao(package, manifest, wordpress_body):
    if not isinstance(package, dict) or not isinstance(manifest, dict):
        raise ValueError("pacote/manifesto invalidos")
    if package.get("stage") not in ("research", "draft"):
        raise ValueError("SEO deve integrar o pacote antes da revisao")
    if package.get("human_acceptance") or package.get("reviews"):
        raise ValueError("ja existe revisao/aceite; iniciar nova versao sem reaproveitar aprovacao")
    payload = package.get("payload")
    if not isinstance(payload, dict) or not isinstance(wordpress_body, str):
        raise ValueError("corpo editorial ausente")
    if (not isinstance(payload.get("content"), str)
            or payload["content"] != wordpress_body
            or not payload["content"].strip()):
        raise ValueError("corpo WordPress diverge da versao que sera revisada")
    if "seo" in payload:
        raise ValueError("SEO ja vinculado; nao sobrepor silenciosamente")
    previous_digest = _digest(payload)
    if package.get("version_sha256") not in (None, previous_digest):
        raise ValueError("versao editorial anterior adulterada")
    if (manifest.get("status") != "aguardando_revisao"
            or manifest.get("wordpress_written") is not False
            or manifest.get("aprovacao_publicacao") is not False):
        raise ValueError("manifesto consultivo invalido ou promovido")
    staging = manifest.get("seo_wp_staging")
    candidate = manifest.get("seo")
    if not isinstance(staging, dict) or not isinstance(candidate, dict):
        raise ValueError("SEO consultivo ausente")
    slug = payload.get("slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug editorial invalido")
    canonical = SITE + "/" + slug + "/"
    if (candidate.get("slug") != slug
            or staging.get("schema_version") != "1.0"
            or staging.get("provider") != "native"
            or staging.get("canonical") != canonical
            or staging.get("delivery_status") != "not_written"
            or staging.get("approved_for_publication") is not False
            or set(staging) != {"schema_version", "provider", "title",
                                "description", "canonical", "delivery_status",
                                "approved_for_publication"}):
        raise ValueError("SEO consultivo nao corresponde ao artigo")
    title = staging["title"]
    description = staging["description"]
    if (not isinstance(title, str) or not title.strip()
            or len(title.strip().encode("utf-8")) > 250
            or not isinstance(description, str) or not description.strip()
            or len(description.strip().encode("utf-8")) > 600
            or not isinstance(candidate.get("title"), str)
            or not isinstance(candidate.get("description"), str)
            or candidate["title"].strip() != title.strip()
            or candidate["description"].strip() != description.strip()):
        raise ValueError("titulo/descricao SEO inconsistentes")
    result = deepcopy(package)
    result["payload"]["seo"] = {
        "provider": "native", "title": title.strip(),
        "description": description.strip(), "canonical": canonical,
    }
    result["version_sha256"] = _digest(result["payload"])
    # Approval, substantive review and presentation are deliberately absent.
    # The Conexo OS editorial validator is the sole authority for readiness.
    return result
