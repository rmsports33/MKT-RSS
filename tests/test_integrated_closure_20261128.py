"""Única matriz integrada: produtor → revisão → scoring → ASVE → sidecar → Gate → writer.

Dados sintéticos. Nenhuma chamada de rede, WordPress ou Turso reais.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from mkt_flow_p0.editorial_gate_traceability import validate_gate_traceability_sidecar
from mkt_flow_p0.wp_quality_executor import review_once
from test_wp_quality_executor import FakeWP, complete_evidence

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ.parent / "site-conexotech-editorial-gate"

DOSSIE = {
    "sources": [{
        "source_id": "s1", "url": "https://www.epe.gov.br/pde", "publisher": "EPE",
        "source_type": "planning_document", "source_role": "primary_origin",
        "published_at": "2026-11-01", "reference_period": "2026-2036",
        "locator": "Caderno de demanda, tabela 1", "methodology": "Cenario EPE publicado",
        "limitations": "Projecao condicionada a premissas",
        "retrieved_at": "2026-11-27T10:00:00Z",
    }],
    "claims": [{
        "claim_id": "c1", "claim_text": "A EPE projeta crescimento.",
        "source_ids": ["s1"], "source_role": "primary_origin",
        "verification_status": "PROJETADA",
    }],
}


def analisador(prompt):
    import re
    from mkt_flow_p0.editorial_secondary_analysis import SCHEMA
    digest = re.search(r'"article_sha256":"([a-f0-9]{64})"', prompt).group(1)
    return {"schema": SCHEMA, "article_sha256": digest, "findings": []}


def php_teste(nome, marcador):
    script = GATE / "tests" / nome
    resultado = subprocess.run(["php", str(script)], capture_output=True,
                               text=True, encoding="utf-8", timeout=30)
    assert resultado.returncode == 0, (nome, resultado.stderr)
    assert marcador in resultado.stdout, (nome, resultado.stdout)


def test_cadeia_integrada_com_consumidor_gate_e_writer_sintetico():
    cliente = FakeWP()
    with tempfile.TemporaryDirectory() as raiz:
        parecer, remoto = review_once(
            cliente, 9768,
            {**complete_evidence(cliente.p), "asve_dossier": DOSSIE,
             "run_id": "run_integrada_2026"},
            str(Path(raiz) / "private.db"), run_asve=True, asve_analyzer=analisador,
        )
    assert remoto is None
    assert parecer["veredito"] == "APTO_PARA_APROVACAO"
    assert parecer["asve_required"] is True
    assert not parecer["publicacao_autorizada"]

    # Scoring diagnóstico vinculado ao parecer e ao texto exato.
    nota = parecer["quality_score_diagnostic"]
    assert nota["fingerprint"] == parecer["fingerprint"]
    assert nota["linked_content_sha256"] == nota["content_sha256"]
    assert not nota["publication_authorized"]

    # Sidecar ASVE íntegro, com run_id e sem autorização.
    sidecar = parecer["gate_traceability_sidecar"]
    assert sidecar["run_id"] == "run_integrada_2026"
    verificado = validate_gate_traceability_sidecar(sidecar)
    assert verificado["valid"] is True
    assert not verificado["publication_authorized"]

    # Consumidor Gate V1 e writer protegido, com dados sintéticos.
    php_teste("test_gate_v1_asve_sidecar.php", "ASVE_SIDECAR_OK")
    php_teste("test_gate_v1_writer_isolado.php", "WRITER_ISOLADO_OK")
    php_teste("test_gate_v1_reviewer_identity.php", "IDENTIDADE_REVISOR_OK")

    # Contraprova: sidecar adulterado é rejeitado pelo validador do produtor.
    adulterado = dict(sidecar)
    adulterado["run_id"] = "run_adulterada_2026"
    try:
        validate_gate_traceability_sidecar(adulterado)
    except ValueError:
        pass
    else:
        raise AssertionError("sidecar adulterado foi aceito")
