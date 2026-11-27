"""Origem da pauta e produtor efetivo devem ser distintos e verificaveis."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from mkt_flow_p0 import editorial_import
from mkt_flow_p0.editorial_identity import (
    criar_handoff_chatgpt, validar_handoff_chatgpt,
)

ARTIGO = {
    "titulo_seo": "Titulo de teste",
    "meta_description": "Descricao com mais de sessenta caracteres para validacao editorial.",
    "slug": "teste-proveniencia",
    "texto_markdown": " ".join(["Texto de apuracao sobre eficiencia energetica no mundo e no Brasil."] * 40),
}


def _handoff(**kw):
    return criar_handoff_chatgpt(
        dict(ARTIGO), url_fonte="https://example.org/fonte", fonte_nome="Fonte",
        contexto_complementar={"sources": []}, **kw)


def test_import_externo_nao_e_autoria_mkt_rss():
    h = _handoff()
    origem = h["metadata"]["origin"]
    assert origem["kind"] == "EXTERNAL_CONTENT"
    assert origem["producer"] == "external"
    validar_handoff_chatgpt(h)


def test_produtor_interno_exige_evidencia_do_texto():
    texto = ARTIGO["texto_markdown"]
    evidencia = {"generation_status": "PASS",
                 "content_sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest()}
    h = _handoff(producer="mkt_rss", origin_kind="QUEUED_RSS",
                 producer_evidence=evidencia)
    validar_handoff_chatgpt(h)

    ruim = _handoff(producer="mkt_rss", origin_kind="QUEUED_RSS",
                    producer_evidence={"generation_status": "PASS"})
    with pytest.raises(ValueError, match="producao interna"):
        validar_handoff_chatgpt(ruim)


def test_import_offline_registra_produtor_externo(tmp_path):
    payload = {"source_url": "https://example.org/fonte", "source_name": "Fonte",
               "research": {"sources": []}, "article": dict(ARTIGO)}
    resultado = editorial_import.processar_artigo_importado(
        payload, tmp_path / "saida", offline=True)
    meta = json.loads((tmp_path / "saida" / "article.metadata.json").read_text(encoding="utf-8"))
    assert meta["origin"]["producer"] == "external"
    assert meta["origin"]["kind"] == "EXTERNAL_CONTENT"
    assert not resultado["provider_called"]


def test_pauta_id_invalido_nao_toca_rede(tmp_path):
    r = subprocess.run(
        [sys.executable, "pipeline_rss.py", "--pauta-id", "invalido",
         "--fonte", "tecnoblog", "--limit", "1",
         "--handoff-only", "--handoff-dir", str(tmp_path / "saida")],
        capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 2
    assert "pauta_id_invalido" in r.stdout
