"""Fail-closed checks: diagnostics never authorize publication."""
import hashlib

from mkt_flow_p0.editorial_voice_adapter import editorial_readiness
from mkt_flow_p0.editorial_substance import assess_editorial_release


def test_no_receipts_never_authorize():
    manuscript = "# Título\n\nTexto para teste."
    result = editorial_readiness(manuscript, {})
    assert result["ready_for_gate"] is False
    assert result["publication_authorized"] is False
    assert result["missing_receipts"]


def test_self_reported_receipts_are_not_authenticated():
    manuscript = "# Título\n\nTexto para teste."
    sha = hashlib.sha256(manuscript.encode("utf-8")).hexdigest()
    names = ("full_article", "introduction_review", "factual_review",
             "source_review", "image_license", "independent_human_review",
             "responsive_390", "responsive_1440", "wordpress_gate_test")
    receipts = {name: {"status": "approved", "content_sha256": sha,
                       "reviewer": "Test reviewer", "evidence": "test evidence",
                       "date": "2026-11-11"} for name in names}
    result = editorial_readiness(manuscript, receipts)
    assert result["missing_receipts"] == []
    assert result["ready_for_gate"] is False
    assert result["publication_authorized"] is False


def test_stale_version_is_rejected():
    manuscript = "# Título\n\nTexto para teste."
    receipt = {"status": "approved", "content_sha256": "0" * 64,
               "reviewer": "Test reviewer", "evidence": "test evidence",
               "date": "2026-11-11"}
    result = editorial_readiness(manuscript, {"full_article": receipt})
    assert "full_article" in result["missing_receipts"]


def test_combined_diagnostic_blocks_without_brief_and_review():
    result = assess_editorial_release("# Título\n\nTexto para teste.", None, None, None)
    assert result["status"] == "BLOCKED"
    assert result["publication_authorized"] is False
    assert result["blockers"]
