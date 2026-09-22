"""
Testes do coletor de specs (fetcher injetado + cache tmp)
pytest redator-artigo-blogs/tests -v
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import src.collectors.websearch_specs as W


def test_curated_e_cache(tmp_path, monkeypatch):
    curated = tmp_path / "cur.json"
    curated.write_text(json.dumps([{"modelo": "Fone A", "specs": {"peso.g": "200"}, "fonte": "fab"}]),
                       encoding="utf-8")
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(W, "CURATED_PATH", curated)
    monkeypatch.setattr(W, "CACHE_PATH", cache)
    r1 = W.buscar_specs("Fone A")
    assert r1["specs"]["peso.g"] == "200" and r1["origem"] == "curated"
    r2 = W.buscar_specs("Fone A")  # agora vem do cache
    assert r2["origem"] == "cache"


def test_fetcher_e_sem_fonte(tmp_path, monkeypatch):
    cache = tmp_path / "c.json"
    monkeypatch.setattr(W, "CACHE_PATH", cache)
    monkeypatch.setattr(W, "CURATED_PATH", tmp_path / "inexistente.json")
    r = W.buscar_specs("Fone Z", fetcher=lambda m, c: {"tela.hz": "120"})
    assert r["specs"]["tela.hz"] == "120" and r["origem"] == "websearch"
    r2 = W.buscar_specs("Fone W")
    assert r2["specs"] == {} and "aviso" in r2


def test_usar_ponte_stub_sem_rede(tmp_path, monkeypatch):
    import sys
    import types
    cache = tmp_path / "c.json"
    monkeypatch.setattr(W, "CACHE_PATH", cache)
    monkeypatch.setattr(W, "CURATED_PATH", tmp_path / "inexistente.json")
    stub = types.ModuleType("src.collectors.ponte_redator")
    stub.buscar_specs = lambda m, c="geral", **k: {"specs": {"tela.hz": "120"},
                                                  "fonte": "fab"}
    monkeypatch.setitem(sys.modules, "src.collectors.ponte_redator", stub)
    r = W.buscar_specs("Fone P", usar_ponte=True)
    assert r["specs"]["tela.hz"] == "120" and r["origem"] == "ponte"
