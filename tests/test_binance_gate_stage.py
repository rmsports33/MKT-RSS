"""MKT-RSS #121: stage-only via canonical Gate, fail-closed.

No test publishes, approves, or calls WordPress. Tests inspect source/contract
as text so they run on any platform (the controller itself is Linux-only).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE_SRC = (ROOT / "ops/hostinger/binance_gate_stage.py").read_text()
CTRL_SRC = (ROOT / "ops/hostinger/remote_controller.py").read_text()
LAUNCHER_SRC = (ROOT / "ops/hostinger/conexo_editorial.sh").read_text()


def test_constants_match_issue_121():
    assert 'EXPECTED_VERSION = "d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2"' in STAGE_SRC
    assert 'EXPECTED_MARKDOWN = "1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60"' in STAGE_SRC
    assert "EXPECTED_MEDIA_ID = 9892" in STAGE_SRC


def test_no_generic_wp_write_or_token_in_code():
    # Strip docstrings/comments before checking for forbidden write calls.
    import re
    code = re.sub(r'""".*?"""', "", STAGE_SRC, flags=re.S)
    code = re.sub(r"(?m)^\s*#.*$", "", code)
    assert "wp/v2/posts" not in code
    assert "wpcom_mcp_posts_create" not in code
    assert "gho_" not in code
    assert "publication_authorized" in STAGE_SRC
    assert 'intent="stage"' in code
    assert "publish_package" in code


def test_idempotency_marker_present():
    assert "ALREADY_ATTEMPTED" in STAGE_SRC
    assert "marker" in STAGE_SRC


def test_controller_allowlist_has_binance_stage():
    assert '"binance_stage": ["--binance-stage"]' in CTRL_SRC
    assert '"binance_stage"' in CTRL_SRC
    assert "WP_CREDENTIAL_ACTIONS" in CTRL_SRC
    assert "keep_wp_credentials" in CTRL_SRC


def test_controller_scrubs_credentials_for_other_actions():
    # Non-binance actions must still drop WP credentials.
    assert "if not keep_wp_credentials:" in CTRL_SRC
    assert "CONEXO_WP_APP_PASSWORD" in CTRL_SRC


def test_launcher_has_binance_stage_flag():
    assert "--binance-stage)" in LAUNCHER_SRC
    assert "binance_gate_stage.py" in LAUNCHER_SRC
