"""Editorial package preflight is diagnostic and cannot authorize a write."""
import pytest
from mkt_flow_p0.editorial_substance import assess_editorial_package


def test_missing_editorial_evidence_blocks_package():
    result = assess_editorial_package({"version_sha256": "v1", "payload": {"content": "# Título\n\nTexto em revisão."}})
    assert result["status"] == "BLOCKED"
    assert result["blockers"]
    assert result["publication_authorized"] is False
    assert result["package_version_sha256"] == "v1"


@pytest.mark.parametrize("package", [None, {}, {"payload": {}}, {"payload": {"content": ""}}])
def test_invalid_or_empty_package_fails_closed(package):
    with pytest.raises(ValueError):
        assess_editorial_package(package)
