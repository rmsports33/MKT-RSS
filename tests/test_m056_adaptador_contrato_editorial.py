"""M05.6: contrato tipado canonico cruza a fronteira somente como snapshot."""
from copy import deepcopy

from mkt_flow_p0.adaptador_contrato_editorial import (
    avaliar_snapshot_editorial,
    normalizar_snapshot_editorial,
)


def _snapshot():
    return {
        "contract_version": "1.0",
        "content_type": "noticia",
        "status": "PASS",
        "sources": [{
            "id": "s1", "status": "PASS", "url": "https://example.org/origem",
            "retrieved_at": "2026-10-23T12:00:00Z", "pending": False,
        }],
        "claims": [{
            "id": "c1", "claim_type": "fact", "text": "A empresa anunciou um produto.",
            "status": "PASS", "evidence_ids": ["s1"], "pending": False,
        }],
    }


def test_snapshot_compativel_apenas_atesta_estrutura():
    assert avaliar_snapshot_editorial(_snapshot())["veredito"] == "EVIDENCIAS_ESTRUTURADAS"


def test_adapter_nao_muta_payload_de_entrada():
    payload = _snapshot()
    antes = deepcopy(payload)
    saida = normalizar_snapshot_editorial(payload)
    saida["claims"][0]["status"] = "FAIL"
    assert payload == antes


def test_versao_tipo_ou_payload_invalido_bloqueia():
    for payload in (None, [], {}, {"contract_version": "2.0"}, {
        **_snapshot(), "content_type": "comparativo"
    }):
        assert avaliar_snapshot_editorial(payload)["veredito"] == "BLOQUEADO"


def test_claim_nao_aprovada_bloqueia():
    payload = _snapshot()
    payload["claims"][0]["status"] = "UNKNOWN"
    assert avaliar_snapshot_editorial(payload)["veredito"] == "BLOQUEADO"


def test_adapter_nao_expoe_autorizacao_de_publicacao():
    resultado = avaliar_snapshot_editorial(_snapshot())
    assert resultado["veredito"] != "PASS"
    assert "escreveu" not in resultado
    assert "publicar" not in resultado
