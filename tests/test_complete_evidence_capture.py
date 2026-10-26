import pytest
from mkt_flow_p0.captura_completa import criar_captura_completa, verificar_captura_completa
from mkt_flow_p0.chatgpt_work_handoff import preparar_pacote_completo

URL = "https://example.org/official"
BODY = " ".join(["Evidence verified at original source."] * 35)


def test_complete_snapshot_keeps_body_hash_and_metadata():
    capture = criar_captura_completa(URL, BODY, titulo="Original")
    assert capture["texto"] == BODY
    assert capture["palavras"] >= 100
    assert capture["status_revisao"] == "PENDENTE"
    assert verificar_captura_completa(capture)


def test_snapshot_rejects_short_excerpt():
    with pytest.raises(ValueError):
        criar_captura_completa(URL, "Short quote", titulo="Original")


def test_snapshot_tampering_rejected():
    capture = criar_captura_completa(URL, BODY, titulo="Original")
    capture["texto"] += " New sentence."
    assert not verificar_captura_completa(capture)


def test_cli_export_contract_requires_full_snapshot():
    contract = {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "s1", "url": URL, "status": "PASS",
                     "retrieved_at": "2026-10-26"}],
        "claims": [{"id": "c1", "text": "Evidence verified at original source.",
                    "status": "PASS", "evidence_ids": ["s1"]}],
    }
    with pytest.raises(ValueError):
        preparar_pacote_completo(contract, {
            "s1": {"url": URL, "texto": "Evidence verified at original source."}
        })
    capture = criar_captura_completa(URL, BODY, titulo="Original")
    pack = preparar_pacote_completo(contract, {"s1": capture})
    assert pack["payload"]["capturas"]["s1"]["texto"] == BODY
    assert len(pack["sha256"]) == 64
