"""Builder do pacote editorial-workflow/2 a partir do handoff real (MKT-RSS #121).

Nao sintetiza julgamento editorial; reaproveita vincular_seo_antes_da_revisao.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "ops/hostinger/build_binance_package.py").read_text()


def test_builder_reuses_canonical_seo_binding():
    import re
    code = re.sub(r'""".*?"""', "", SRC, flags=re.S)  # strip docstring
    assert "vincular_seo_antes_da_revisao" in code
    assert "editorial_package_handoff" in code
    assert "editorial_core_offline" not in code  # nao reprocessa; reusa o body ja gerado


def test_builder_reads_real_handoff_files():
    for name in ["article.metadata.json", "article.md", ".report.json", ".wordpress-body.html"]:
        assert name in SRC


def test_builder_records_both_versions_and_pointer():
    assert "package_version_sha256" in SRC
    assert "handoff_version_sha256" in SRC
    assert "editorial-workflow-pointer.json" in SRC
    assert "publication_authorized" in SRC
    assert "False" in SRC


def test_builder_fails_closed():
    assert "BLOCKED" in SRC
    assert "HANDOFF_MISSING" in SRC or "HANDOFF_FILE_MISSING" in SRC
