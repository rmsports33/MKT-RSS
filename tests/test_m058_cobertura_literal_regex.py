"""M05.8: contraprovas do gate de cobertura literal, offline."""
from mkt_flow_p0.produtor_evidencias_noticia import produzir_contrato_noticia


def _contrato():
    return {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{
            "id": "s1", "url": "https://example.org/fonte",
            "retrieved_at": "2026-10-23", "status": "PASS",
        }],
        "claims": [{
            "id": "c1", "status": "PASS", "evidence_ids": ["s1"],
            "text": "A empresa apresentou o dispositivo.",
        }],
    }


def test_frase_extra_na_mesma_linha_e_bloqueada():
    texto = "A empresa apresentou o dispositivo. A bateria dura 99 horas."
    assert produzir_contrato_noticia(_contrato(), texto) is None


def test_titulo_markdown_com_alegacao_extra_e_bloqueado():
    texto = "# A bateria dura 99 horas.\nA empresa apresentou o dispositivo."
    assert produzir_contrato_noticia(_contrato(), texto) is None


def test_lista_markdown_e_bloqueada_sem_parser():
    texto = "A empresa apresentou o dispositivo.\n- Bateria: 99 horas"
    assert produzir_contrato_noticia(_contrato(), texto) is None


def test_frase_aprovada_com_espacos_e_aceita():
    texto = "A empresa  apresentou o dispositivo."
    assert produzir_contrato_noticia(_contrato(), texto) is not None


def test_frase_aprovada_em_heading_e_aceita():
    texto = "# A empresa apresentou o dispositivo."
    assert produzir_contrato_noticia(_contrato(), texto) is not None
