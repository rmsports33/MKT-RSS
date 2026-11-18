"""Integracao: contrato editorial, video, proveniencia, preview e CLI offline."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mkt_flow_p0 import editorial_provenance as pv
from mkt_flow_p0.editorial_import import _parser, processar_artigo_importado
from mkt_flow_p0.seo import validar_artigo_wordpress


def payload():
    return {
        "source_url": "https://example.org/source",
        "source_name": "Primary source",
        "article": {
            "titulo_seo": "Guia editorial documentado",
            "meta_description": (
                "Guia documentado e atribuído com explicações práticas e limites "
                "claros, pendente de revisão humana antes da publicação."
            ),
            "slug": "guia-editorial-documentado",
            "texto_markdown": (
                "## Primeira seção\n\n"
                + ("Explicação clara e atribuída para leitores, sem experiência "
                   "inventada ou promessa de resultado. " * 22)
                + "\n\n## Comparação\n\n| Opção | Uso |\n|---|---|\n"
                  "| Exemplo | Explicação |"
            ),
        },
        "research": {"sources": [{
            "name": "Fonte adicional",
            "url": "https://example.com/additional",
            "facts": ["Uma fonte documenta o recurso explicado e suas limitações."],
        }]},
    }


def payload_com_video():
    dados = payload()
    dados["article"].update({
        "youtube_id": "dQw4w9WgXcQ",
        "youtube_titulo": "Review real do aparelho",
        "youtube_canal": "Canal real",
        "youtube_resumo": "Mostra o aparelho ligado em uso.",
        "youtube_duracao": "8:32",
    })
    return dados


def contrato_pendente():
    return {
        "contract_version": "1.0",
        "content_type": "noticia",
        "status": "PENDING",
        "sources": [{
            "id": "src-1", "url": "https://example.org/source",
            "status": "PENDING", "pending": True, "retrieved_at": None,
        }],
        "claims": [{
            "id": "extra_1_1",
            "text": "Uma fonte documenta o recurso explicado e suas limitações.",
            "status": "PENDING", "pending": True, "heuristic": False,
            "evidence_ids": [],
        }],
    }


def processar(dados, destino):
    with patch("socket.create_connection",
               side_effect=AssertionError("rede proibida no teste")):
        return processar_artigo_importado(dados, destino)


def test_contrato_editorial_restaurado(tmp_path):
    dados = payload()
    dados["editorial_contract"] = contrato_pendente()
    resultado = processar(dados, tmp_path / "v")
    # Antes da correcao a chave extra reprovava o pacote inteiro.
    assert "contrato_editorial_ausente" not in resultado["evidence_contract"]["motivos"]
    assert resultado["evidence_contract"]["veredito"] == "BLOQUEADO"
    metadados = json.loads(Path(resultado["metadata_path"]).read_text(encoding="utf-8"))
    assert metadados["contrato_editorial"]["contract_version"] == "1.0"
    assert metadados["contrato_editorial"]["status"] == "PENDING"


def test_video_da_ficha_chega_ao_corpo_e_ao_preview(tmp_path):
    resultado = processar(payload_com_video(), tmp_path / "v")
    corpo = Path(resultado["wordpress_body_path"]).read_text(encoding="utf-8")
    preview = Path(resultado["preview_path"]).read_text(encoding="utf-8")
    assert resultado["video_review"]["status"] == "INSERIDO_COM_CURADORIA_HUMANA"
    assert resultado["video_review"]["youtube_id"] == "dQw4w9WgXcQ"
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in corpo
    assert '"duration": "PT8M32S"' in corpo
    assert "Duração: 8:32" in corpo
    assert "<iframe" in preview
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in preview


def test_preview_e_body_compartilham_o_mesmo_fragmento(tmp_path):
    resultado = processar(payload_com_video(), tmp_path / "v")
    corpo = Path(resultado["wordpress_body_path"]).read_text(encoding="utf-8")
    preview = Path(resultado["preview_path"]).read_text(encoding="utf-8")
    assert corpo in preview
    marca_body = pv.extrair_manifesto(corpo)
    marca_preview = pv.extrair_manifesto(preview)
    assert marca_body == marca_preview == resultado["provenance_manifest"]


def test_sem_video_nada_e_inserido(tmp_path):
    resultado = processar(payload(), tmp_path / "v")
    corpo = Path(resultado["wordpress_body_path"]).read_text(encoding="utf-8")
    assert resultado["video_review"] == {"status": "SEM_VIDEO_VALIDO", "inserido": False}
    assert "<iframe" not in corpo
    assert "application/ld+json" not in corpo


def test_readiness_e_seo_refletem_o_corpo_final(tmp_path):
    sem = processar(payload(), tmp_path / "sem")
    com = processar(payload_com_video(), tmp_path / "com")
    assert (com["readiness"]["subtitulos_h2"]
            == sem["readiness"]["subtitulos_h2"] + 1)
    corpo = Path(com["wordpress_body_path"]).read_text(encoding="utf-8")
    metadados = json.loads(Path(com["metadata_path"]).read_text(encoding="utf-8"))
    assert com["seo_preflight"] == validar_artigo_wordpress(
        metadados["title"], corpo, tem_capa=False)


def test_proveniencia_reprova_import_sem_voz_aplicada(tmp_path):
    resultado = processar(payload_com_video(), tmp_path / "v")
    corpo = Path(resultado["wordpress_body_path"]).read_text(encoding="utf-8")
    assert pv.validar(corpo) == {"valido": False, "motivo": "voz_nao_aplicada"}
    assert resultado["publication_authorized"] is False
    assert resultado["human_acceptance"] == "PENDING"


def test_hash_publicado_confere_com_a_marca(tmp_path):
    resultado = processar(payload_com_video(), tmp_path / "v")
    corpo = Path(resultado["wordpress_body_path"]).read_text(encoding="utf-8")
    sem_marca = pv.PADRAO.sub("", corpo)
    assert resultado["wordpress_body_sha256"] == pv.hash_corpo(sem_marca)
    assert resultado["provenance_manifest"]["content_sha256"] == pv.hash_corpo(sem_marca)
    assert resultado["provenance_manifest"]["version_sha256"] == resultado["version_sha256"]


def test_cli_inicia_offline_e_exige_online_explicito(tmp_path):
    parser = _parser()
    padrao = parser.parse_args(["--import-article", "a.json", "--handoff-dir", "d"])
    assert padrao.offline is True
    compativel = parser.parse_args(
        ["--import-article", "a.json", "--handoff-dir", "d", "--offline"])
    assert compativel.offline is True
    online = parser.parse_args(
        ["--import-article", "a.json", "--handoff-dir", "d", "--online"])
    assert online.offline is False
