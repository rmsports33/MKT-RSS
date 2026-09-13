"""
Testes — scripts/atualizar_fichas.py (usa tmp_path, sem rede)
pytest tests/unit/test_atualizar_fichas.py -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def _setup_tmp(tmp_path, monkeypatch):
    import scripts.atualizar_fichas as A
    fake_curated = tmp_path / "curated.json"
    monkeypatch.setattr(A, "CURATED", fake_curated)
    return A


def test_criar_e_atualizar(tmp_path, monkeypatch, capsys):
    A = _setup_tmp(tmp_path, monkeypatch)
    A.salvar_ficha("Fone X", "audio", {"bateria.mah": "5000"}, "fab X")
    out = json.loads(capsys.readouterr().out)
    assert out["acao"] == "criada"
    A.salvar_ficha("Fone X", "audio", {"bateria.mah": "6000"}, "fab X")
    out = json.loads(capsys.readouterr().out)
    assert out["acao"] == "atualizada"
    data = json.loads((tmp_path / "curated.json").read_text(encoding="utf-8"))
    assert data[0]["specs"]["bateria.mah"] == "6000"


def test_remover(tmp_path, monkeypatch, capsys):
    A = _setup_tmp(tmp_path, monkeypatch)
    A.salvar_ficha("Fone Y", "audio", {"peso.g": "200"}, "fab Y")
    capsys.readouterr()
    A.remover("Fone Y")
    assert json.loads(capsys.readouterr().out)["acao"] == "removida"
    assert json.loads((tmp_path / "curated.json").read_text(encoding="utf-8")) == []


def test_main_via_specs(tmp_path, monkeypatch):
    import scripts.atualizar_fichas as A
    fake = tmp_path / "cur.json"
    monkeypatch.setattr(A, "CURATED", fake)
    with patch.object(sys, "argv", ["prog", "--modelo", "M", "--categoria", "celular", "--specs", '{"a":"1"}', "--fonte", "f"]):
        A.main()
    assert json.loads(fake.read_text(encoding="utf-8"))[0]["modelo"] == "M"
