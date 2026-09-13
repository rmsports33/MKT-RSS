"""
Testes — backup_drive (offline: seleção e zip)
pytest tests/test_backup_drive.py -v
"""
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backup_drive import coletar_arquivos, empacotar


def test_coletar_so_existentes(tmp_path):
    (tmp_path / "sitemap.xml").write_text("<x/>", encoding="utf-8")
    achados = coletar_arquivos(tmp_path)
    assert any(a.endswith("sitemap.xml") for a in achados)
    assert not any(a.endswith("mkt_flow_p0.db") for a in achados)


def test_empacotar(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("oi", encoding="utf-8")
    z = empacotar([str(f)], tmp_path)
    assert zipfile.is_zipfile(z)
    assert "a.txt" in zipfile.ZipFile(z).namelist()
