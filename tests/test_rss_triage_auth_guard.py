"""Security: command-line editorial writes are disabled without verified identity."""
import sys
import pytest
import rss_editorial_triage as cli


def test_cli_decision_denied_even_with_claimed_operator(monkeypatch, capsys):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://" + cli.HOST_HOMOLOG)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "fake-token-offline")
    monkeypatch.setattr(sys, "argv", [
        "rss_editorial_triage.py", "--homolog", "--acao", "selecionar",
        "--pauta-id", "a" * 32, "--justificativa", "Fonte verificada",
        "--operador", "editor-01", "--confirm",
    ])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "identidade e autorizacao autenticadas" in capsys.readouterr().out


def test_default_read_only_still_available(monkeypatch, capsys):
    monkeypatch.setattr(cli, "listar", lambda **kwargs: [])
    monkeypatch.setattr(sys, "argv", ["rss_editorial_triage.py", "--limit", "3"])
    cli.main()
    assert '"modo": "somente_leitura"' in capsys.readouterr().out
