"""Testes offline: origem da autoria, EXECUTED vs PASS e direitos de imagem.

Nenhum teste chama rede, provedor ou WordPress; o bloqueio de socket é apenas
uma rede de segurança adicional quando o fluxo offline é executado de fato.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mkt_flow_p0.editorial_import import (
    normalizar_proveniencia_autoria,
    processar_artigo_importado,
    separar_execucao_aprovacao,
)

VALID = {"tool": "codex-cloud", "version": "1.2.3", "input_sha256": "a" * 64}


def payload():
    return {
        "source_url": "https://example.org/source",
        "source_name": "Primary source",
        "article": {
            "titulo_seo": "Documented editorial guide",
            "meta_description": "A documented and attributed guide with practical explanations and clear limits, pending human editorial review before publication.",
            "slug": "documented-editorial-guide",
            "texto_markdown": "## First section\n\n" + (
                "Clear sourced explanation for readers, with no invented experience or claims. " * 22
            ) + "\n\n## Comparison\n\n| Option | Purpose |\n|---|---|\n| Example | Explanation |",
        },
        "research": {"sources": [
            {"name": "Additional source", "url": "https://example.com/additional",
             "facts": ["A source documents the explained feature and its limitations."]},
        ]},
    }


def processar(p, out, **kwargs):
    with patch("socket.create_connection", side_effect=AssertionError("Unexpected network")):
        return processar_artigo_importado(p, out, **kwargs)


# --- item 1: origem da autoria (função auxiliar pura) ------------------------

def test_origem_ausente_nao_registrada():
    assert normalizar_proveniencia_autoria(None) == {
        "status": "NAO_REGISTRADA",
        "reason": "prewritten_import_sem_prova_de_origem",
    }


@pytest.mark.parametrize("invalida", [
    {"tool": "", "version": "1.0", "input_sha256": "a" * 64},
    {"tool": "x" * 81, "version": "1.0", "input_sha256": "a" * 64},
    {"tool": "codex", "version": "1.0", "input_sha256": "abc123"},
    {"tool": "codex", "version": "1.0", "input_sha256": "A" * 64},
    {"tool": "codex", "input_sha256": "a" * 64},
    "nao-e-dict",
])
def test_origem_invalida_recusada(invalida):
    with pytest.raises(ValueError):
        normalizar_proveniencia_autoria(invalida)


def test_origem_valida_nao_infere_modelo():
    normalizada = normalizar_proveniencia_autoria(dict(VALID))
    assert normalizada == {"status": "REGISTRADA", **VALID}
    assert "model" not in normalizada


def test_origem_valida_aparece_no_resultado_e_no_trace(tmp_path):
    p, p["authoring_provenance"] = payload(), dict(VALID)
    result = processar(p, tmp_path / "com-origem")
    assert result["authoring_provenance"]["status"] == "REGISTRADA"
    assert result["authoring_provenance"]["tool"] == VALID["tool"]

    # A prova não entra no handoff: metadados são validados de forma rígida.
    handoff = json.loads(Path(result["handoff_path"]).read_text(encoding="utf-8"))
    assert "authoring_provenance" not in handoff["metadata"]

    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
    eventos = [e for e in trace["events"] if e["stage"] == "authoring"]
    assert any(e["status"] == "REGISTRADA" and e.get("input_sha256") == VALID["input_sha256"]
               for e in eventos)
    # Evento existente permanece intacto.
    assert trace["events"][0]["module_id"] == "mkt-rss.editorial-import"
    assert trace["events"][0]["status"] == "IMPORTED_NO_PROVIDER"


def test_origem_ausente_aparece_como_nao_registrada_no_resultado_e_trace(tmp_path):
    result = processar(payload(), tmp_path / "sem-origem")
    assert result["authoring_provenance"] == {
        "status": "NAO_REGISTRADA",
        "reason": "prewritten_import_sem_prova_de_origem",
    }
    trace = json.loads(Path(result["trace_path"]).read_text(encoding="utf-8"))
    assert any(e["stage"] == "authoring" and e["status"] == "NAO_REGISTRADA"
               and e.get("reason") == "prewritten_import_sem_prova_de_origem"
               for e in trace["events"])


# --- item 5: EXECUTED não é PASS ---------------------------------------------

def test_separacao_conservadora_de_execucao_e_aprovacao():
    manifest = [
        {"id": "editorial_import", "execution": "EXECUTED", "outcome": "DIAGNOSTIC_ONLY"},
        {"id": "editorial_readiness", "execution": "EXECUTED", "outcome": "PRONTO_PARA_REVISAO_HUMANA"},
        {"id": "gate_editorial_pos_ia", "execution": "EXECUTED", "outcome": "PASS"},
        {"id": "image_protocol", "execution": "EXECUTED", "outcome": "PENDING_IMAGE"},
        {"id": "editorial_substance", "execution": "EXECUTED", "outcome": "PENDING"},
        {"id": "alias_de_aprovacao", "execution": "EXECUTED", "outcome": "APPROVED"},
    ]
    separacao = separar_execucao_aprovacao(manifest)
    assert separacao["executed"] == [m["id"] for m in manifest]
    assert separacao["passed"] == ["editorial_readiness", "gate_editorial_pos_ia"]
    assert "EXECUTADO não é APROVADO" in separacao["note"]


def test_execution_vs_approval_do_resultado_nao_autoriza_publicacao(tmp_path):
    result = processar(payload(), tmp_path / "out")
    separacao = result["execution_vs_approval"]
    assert separacao["executed"] == [m["id"] for m in result["module_manifest"]]
    assert set(separacao["passed"]).issubset(set(separacao["executed"]))
    assert "image_protocol" not in separacao["passed"]
    assert "editorial_import" not in separacao["passed"]
    assert result["publication_authorized"] is False
    assert result["human_acceptance"] == "PENDING"


# --- item 9: direitos de imagem no pacote ------------------------------------

def test_confirmacao_de_direitos_exige_parametro_explicito(tmp_path):
    evidence = {"fonte": "licença documentada", "url": "https://example.org/licenca"}
    sem = processar(payload(), tmp_path / "sem-confirmacao", image_rights_evidence=evidence)
    com = processar(payload(), tmp_path / "com-confirmacao", featured_media_id=12,
                    media_rights_confirmed=True, image_rights_evidence=evidence)
    assert sem["image_rights"] == {"confirmed": False, "featured_media_id": None,
                                   "evidence": evidence}
    assert com["image_rights"] == {"confirmed": True, "featured_media_id": 12,
                                   "evidence": evidence}


def test_midia_destacada_sem_confirmacao_e_recusada_sem_efeito(tmp_path):
    out = tmp_path / "recusado"
    with pytest.raises(ValueError, match="sem autorização explícita"):
        processar(payload(), out, featured_media_id=12,
                  image_rights_evidence={"fonte": "evidence sem confirmação"})
    assert not out.exists()
