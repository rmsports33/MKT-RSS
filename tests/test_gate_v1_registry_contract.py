"""Teste de compatibilidade do contrato do registro assinado (Gate V1 ↔ MKT-RSS).

Valida estaticamente que o include aditivo do Gate produz exatamente os campos
que `editorial_trusted_review.verify_independent_review()` exige.
"""
from pathlib import Path

BASE = Path(__file__).parent.parent


def _php():
    return (BASE / "mkt_flow_p0" / "gate_v1_registry_route.php").read_text(encoding="utf-8")


def test_campos_exigidos_pelo_mkt_rss():
    php = _php()
    for campo in (
        "reviewer_id", "draft_sha256", "decision", "status",
        "independent", "evidence_refs", "review_record_url", "revoked",
    ):
        assert f"'{campo}'" in php, campo


def test_valores_exigidos():
    php = _php()
    assert "'decision' => 'APROVADO'" in php
    assert "'status' => 'FINAL'" in php
    assert "'independent' => true" in php
    assert "'revoked' => false" in php


def test_hmac_com_chave_separada():
    php = _php()
    assert "CONEXO_REVIEW_REGISTRY_KEY" in php
    assert "hash_hmac('sha256'" in php
    assert "JSON_UNESCAPED_SLASHES" in php
    assert "JSON_UNESCAPED_UNICODE" in php
    assert "JSON_UNESCAPED_LINE_TERMINATORS" in php


def test_sem_segredo_na_resposta():
    php = _php()
    # A resposta contém apenas record + signature; nunca a chave.
    resposta = php[php.index("function cxeg_registry_read"):]
    assert "CONEXO_REVIEW_REGISTRY_KEY" not in resposta.split("$response =")[1]


def test_rota_get_autenticada():
    php = _php()
    assert "register_rest_route('conexo/v1', '/editorial/registry/" in php
    assert "'methods' => 'GET'" in php
    assert "permission_callback" in php
    assert "current_user_can('edit_post'" in php


def test_sem_parecer_vigente_bloqueia():
    php = _php()
    assert "cxeg_quality_valid" in php
    assert "cxeg_registry_no_review" in php
    assert "404" in php
