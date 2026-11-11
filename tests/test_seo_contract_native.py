"""Testes do contrato SEO, sem rede e sem plugin."""
import pytest
from mkt_flow_p0.seo_contract_native import contrato_seo_nativo, contrato_seo_staging_wordpress

def _a():
    return {"seo":{"slug":"android-drop","title":"Android Drop no Brasil","description":"Confira os requisitos documentados do Android Drop."}}

def test_independente_do_plugin():
    c=contrato_seo_nativo(_a())
    assert c["provider"]=="native"
    assert c["plugin_required"] is False
    assert c["canonical"]=="https://conexotech.com.br/android-drop/"
    assert c["delivery_status"]=="not_written"
    assert c["approved_for_publication"] is False
    assert c["robots"]=="noindex,nofollow"

def test_slug_inseguro_falha():
    a=_a(); a["seo"]["slug"]="../admin"
    with pytest.raises(ValueError):
        contrato_seo_nativo(a)

def test_site_origin_insegura_falha():
    with pytest.raises(ValueError):
        contrato_seo_nativo(_a(),site_origin="http://example.com")

def test_descricao_vazia_falha():
    a=_a(); a["seo"]["description"]=" "
    with pytest.raises(ValueError):
        contrato_seo_nativo(a)


def test_staging_rest_corresponde_ao_wordpress_e_nao_publica():
    contract = contrato_seo_nativo(_a())
    staging = contrato_seo_staging_wordpress(contract)
    assert set(staging) == {"schema_version", "provider", "title", "description",
                             "canonical", "delivery_status", "approved_for_publication"}
    assert staging["canonical"] == "https://conexotech.com.br/android-drop/"
    assert staging["approved_for_publication"] is False
    assert staging["delivery_status"] == "not_written"
    assert "robots" not in staging
    assert "rank_math" not in str(staging).lower()

def test_staging_rejeita_promocao_indevida():
    contract = contrato_seo_nativo(_a())
    contract["approved_for_publication"] = True
    with pytest.raises(ValueError, match="nao pode estar aprovado"):
        contrato_seo_staging_wordpress(contract)

def test_staging_rejeita_canonical_externo():
    contract = contrato_seo_nativo(_a())
    contract["canonical"] = "https://evil.example/android-drop/"
    with pytest.raises(ValueError, match="Canonical"):
        contrato_seo_staging_wordpress(contract)
