"""
backup_drive.py — Backup semanal do núcleo no Google Drive (item 11).
Sobe .db + JSON do dashboard + policies. OAuth na primeira execução
(abre o navegador uma vez; depois usa token.json).

Uso: python backup_drive.py [--pasta "MKT-Flow-Backup"]
Requer no .env: GOOGLE_DRIVE_CLIENT_ID e GOOGLE_DRIVE_CLIENT_SECRET.
Nunca commitar token.json/credentials.json (já no .gitignore).
"""
import argparse
import json
import logging
import os
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backup_drive")

ROOT = Path(__file__).parent
ARQUIVOS_BASE = ["mkt_flow_p0.db", "dashboard_p1.json", "sitemap.xml", "llms.txt"]


def coletar_arquivos(root: Path = ROOT) -> list:
    """Lista o que existe (e o pacote policies/). Puro e testável."""
    achados = [str(root / nome) for nome in ARQUIVOS_BASE if (root / nome).exists()]
    pol = root / "mkt_flow_p0" / "policies"
    if pol.exists():
        achados += [str(p) for p in sorted(pol.glob("*.json"))]
    return achados


def empacotar(arquivos: list, destino: Path) -> Path:
    zip_path = destino / f"mktflow-backup-{date.today().isoformat()}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for a in arquivos:
            z.write(a, arcname=Path(a).name)
    return zip_path


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Backup do núcleo no Google Drive")
    ap.add_argument("--pasta", default="MKT-Flow-Backup")
    args = ap.parse_args()

    cid = os.getenv("GOOGLE_DRIVE_CLIENT_ID", "").strip()
    csec = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET", "").strip()
    if not cid or not csec:
        print(json.dumps({"erro": "GOOGLE_DRIVE_CLIENT_ID/SECRET ausentes no .env — ver docs/BACKUP_DRIVE.md"}))
        sys.exit(2)
    arquivos = coletar_arquivos()
    if not arquivos:
        print(json.dumps({"erro": "nada para backup (rode o pipeline/dashboard primeiro)"}))
        sys.exit(3)
    tmp = Path(tempfile.mkdtemp())
    zip_path = empacotar(arquivos, tmp)
    try:
        sys.path.insert(0, str(ROOT))
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient(cid, csec)
        up = client.upload_file(str(zip_path), args.pasta) if hasattr(client, "upload_file") else None
        print(json.dumps({"backup": str(zip_path), "drive": up or {"pasta": args.pasta}}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"erro": f"Upload falhou: {str(e)[:200]}", "zip_local": str(zip_path)}))
        sys.exit(4)


if __name__ == "__main__":
    main()
