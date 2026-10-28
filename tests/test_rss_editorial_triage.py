"""Tests offline da listagem P1. Nenhuma rede, Turso ou WordPress."""
import pytest
import rss_editorial_triage as cli


def test_consulta_lista_apenas_descobertas(monkeypatch):
    calls = []
    def fake_listar(**kwargs):
        calls.append(kwargs)
        return [{"id": "a", "fonte": "feed", "url": "https://example.org/a",
                 "titulo": "Noticia", "estado": "DESCOBERTA", "pontuacao": 55}]
    monkeypatch.setattr(cli, "listar", fake_listar)
    result = cli.consultar(3)
    assert calls == [{"estado": "DESCOBERTA", "limite": 3}]
    assert result["total"] == 1
    assert result["modo"] == "somente_leitura"
    assert "heuristica" in result["pontuacao"]
    assert result["pautas"][0]["estado"] == "DESCOBERTA"


@pytest.mark.parametrize("limit", [0, -1, 21, 100])
def test_limite_invalido_bloqueado(monkeypatch, limit):
    monkeypatch.setattr(cli, "listar", lambda **kwargs: pytest.fail("nao consultar"))
    with pytest.raises(ValueError):
        cli.consultar(limit)


@pytest.mark.parametrize("url,token", [
    ("", ""), ("libsql://mkt-rss-rmsports33.aws-ap-northeast-1.turso.io", "token"),
    ("https://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io", "token"),
    ("libsql://mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io", ""),
])
def test_homolog_falha_fechada(monkeypatch, url, token):
    monkeypatch.setenv("TURSO_DATABASE_URL", url)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", token)
    monkeypatch.setattr(cli, "listar", lambda **kwargs: pytest.fail("nao consultar"))
    with pytest.raises(RuntimeError):
        cli.consultar(3, exigir_homolog=True)


def test_homolog_consulta_somente_apos_guard(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://"+cli.HOST_HOMOLOG)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-de-teste")
    monkeypatch.setattr(cli, "listar", lambda **kwargs: [])
    assert cli.consultar(3, exigir_homolog=True)["total"] == 0
