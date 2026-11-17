"""MKT-RSS #111: o sinal PRONTO_PARA_REVISAO nasce do readback, nunca da existência do rascunho.

Nenhum teste aqui autoriza publicação. Apenas prova que o classificador
de prontidão reusa o validador canônico e não inventa PASS.
"""
from unittest.mock import MagicMock

from mkt_flow_p0.wp_draft_staging import _readiness_from_readback


def _readback(*, complete=True):
    return {
        "id": 123, "status": "draft", "slug": "materia-teste",
        "title": {"raw": "Titulo completo e suficientemente longo para revisao"},
        "content": {"raw": "<p>" + ("texto verificavel " * 80) +
                    '</p><p><a href="https://fonte-externa.com.br">Fonte</a></p>'},
        "excerpt": {"raw": "Resumo SEO com mais de sessenta caracteres descritivos o bastante."},
        "categories": [10], "featured_media": 456,
        "link": "https://conexotech.com.br/?p=123",
    }


def test_incomplete_draft_is_not_marked_ready():
    post = _readback()
    post["content"] = {"raw": "<p>curto</p>"}
    out = _readiness_from_readback(post, featured_media_id=456,
                                   image_caption="Foto: autor, fonte, licença CC BY 4.0")
    assert out["pronto_para_revisao"] is False
    assert isinstance(out["motivo_prontidao"], list)
    assert any("incomplete" in str(x) or "missing" in str(x) for x in out["motivo_prontidao"])


def test_classifier_never_authorizes_publication():
    out = _readiness_from_readback(_readback(), featured_media_id=456,
                                   image_caption="Foto: autor, fonte, licença CC BY 4.0")
    assert set(out) == {"pronto_para_revisao", "motivo_prontidao", "revisao_pos_ia"}
    assert "publication_authorized" not in out
    assert "autorizado" not in out
    assert out["revisao_pos_ia"]["avaliado"] is False


def test_quality_reviewer_blocks_on_unbacked_claim():
    post = _readback()
    post["content"] = {"raw": "<p>" + ("texto verificavel " * 80) +
                       "</p><p>Em nossos testes, o aparelho durou 40 horas.</p>"}
    out = _readiness_from_readback(
        post, featured_media_id=456,
        image_caption="Foto: autor, fonte, licença CC BY 4.0",
        texto_fonte="<p>Texto da fonte sem menção a testes próprios nem 40 horas.</p>")
    assert out["revisao_pos_ia"]["avaliado"] is True
    assert out["pronto_para_revisao"] is False
    assert any("revisao_pos_ia" in str(x) for x in out["motivo_prontidao"])


def test_no_source_does_not_fabricate_review():
    out = _readiness_from_readback(_readback(), featured_media_id=456,
                                   image_caption="Foto: autor, fonte, licença CC BY 4.0")
    assert out["revisao_pos_ia"] == {"avaliado": False, "achados": []}


def test_missing_validator_fails_closed():
    import mkt_flow_p0.wp_draft_staging as w
    import builtins
    real_import = builtins.__import__
    def fake_import(name, *a, **k):
        if name == "editorial_wordpress_readiness":
            raise ImportError("indisponivel")
        return real_import(name, *a, **k)
    builtins.__import__ = fake_import
    try:
        out = w._readiness_from_readback(_readback())
        assert out["pronto_para_revisao"] is False
        assert out["motivo_prontidao"] == "validador_indisponivel"
    finally:
        builtins.__import__ = real_import
