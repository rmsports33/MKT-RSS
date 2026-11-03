"""Contraprovas offline do envelope privado SEO; não faz acesso ao WordPress."""
import hashlib
import hmac
import json
import pytest
from mkt_flow_p0.seo_delivery_signing import prepare_signed_seo_contract

KEY = b"only-for-offline-tests-minimum-32-bytes-signing-key"

def _setup():
    content = "<p>Texto editorial revisado, imutável.</p>"
    package = {
        "stage": "ready", "version_sha256": "a"*64,
        "payload": {"title": "Título editorial", "content": content,
                    "slug": "materia-revisada",
                    "seo": {"title": "Título SEO aprovado",
                            "description": "Descrição SEO aprovada"}}
    }
    snapshot = {"ID": 9711, "post_type": "post", "post_status": "publish",
                "post_name": "materia-revisada", "post_title": "Título editorial",
                "post_content": content}
    result = {"post_id": 9711, "status": "publish", "intent": "publish",
              "editorial_delivered": True, "retry_automatic": False,
              "version_sha256": "a"*64,
              "link": "https://conexotech.com.br/materia-revisada/",
              "snapshot": snapshot}
    return package, result

def test_seo_contract_is_signed_for_exact_post_bytes():
    package, result = _setup()
    signed = prepare_signed_seo_contract(package, result, seo_key=KEY)
    assert signed["content_sha256"] == hashlib.sha256(
        package["payload"]["content"].encode("utf-8")).hexdigest()
    assert signed["approved_for_publication"] is True
    assert signed["delivery_status"] == "approved"
    body = {"domain": "conexo-seo-v1", "post_id": 9711,
            "canonical": signed["canonical"], "title": signed["title"],
            "description": signed["description"],
            "content_sha256": signed["content_sha256"]}
    expected = hmac.new(KEY,json.dumps(body,ensure_ascii=False,
                        separators=(",", ":")).encode("utf-8"),hashlib.sha256).hexdigest()
    assert signed["signature"] == expected
    assert set(signed).isdisjoint({"rank_math_title", "rank_math_description"})

@pytest.mark.parametrize("change", ["stage", "draft", "actor", "content", "seo",
                                    "canonical", "version", "key", "id", "slug"])
def test_refuse_unverified_or_mutated_publishing_receipt(change):
    package, result = _setup()
    key = KEY
    if change == "stage": package["stage"] = "pending"
    elif change == "draft": result["status"] = "draft"
    elif change == "actor": result["editorial_delivered"] = False
    elif change == "content": result["snapshot"]["post_content"] += " changed"
    elif change == "seo": package["payload"].pop("seo")
    elif change == "canonical": result["link"] = "https://evil.example/materia-revisada/"
    elif change == "version": result["version_sha256"] = "b"*64
    elif change == "key": key = b"short"
    elif change == "id": result["snapshot"]["ID"] = 100
    elif change == "slug": result["snapshot"]["post_name"] = "outro"
    with pytest.raises(ValueError):
        prepare_signed_seo_contract(package, result, seo_key=key)

def test_staging_never_gets_signed():
    package, result = _setup()
    result["intent"] = "stage"
    with pytest.raises(ValueError, match="recibo"):
        prepare_signed_seo_contract(package, result, seo_key=KEY)
