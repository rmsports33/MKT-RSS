"""
mkt_flow_p0.health_check — Verificação integrada do núcleo consolidado.
Uso:
  python -m mkt_flow_p0.health_check            # checa tudo
  python -m mkt_flow_p0.health_check --json     # saída JSON
Checa: .env, DB (tabelas do núcleo), regras de policy carregadas, e WP se configurado.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))


def check_env():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "MKTFLOW" / ".env", override=False)
    wp = ["WP_URL", "WP_USER", "WP_APP_PASSWORD"]
    wp_missing = [k for k in wp if not os.getenv(k, "").strip()]
    groq_missing = [] if os.getenv("GROQ_API_KEY", "").strip() else ["GROQ_API_KEY"]
    return {
        "wp_missing": wp_missing,
        "groq_missing": groq_missing,
        "wp_ok": len(wp_missing) == 0,
        "groq_ok": len(groq_missing) == 0,
    }


def check_db():
    try:
        import sqlite3
        dbp = ROOT / "mkt_flow_p0.db"
        if not dbp.exists():
            return {"ok": False, "erro": f"DB ausente: {dbp}"}
        con = sqlite3.connect(dbp)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = {r[0] for r in cur.fetchall()}
        con.close()
        # núcleo: pipeline_runs + link_publicacoes (A); MKTFLOW clássico tem as demais
        faltando = [t for t in ("pipeline_runs", "link_publicacoes") if t not in tabelas]
        if faltando:
            return {"ok": False, "erro": f"tabelas ausentes: {faltando}"}
        return {"ok": True, "tabelas": sorted(tabelas)}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:150]}


def check_policy():
    try:
        from mkt_flow_p0.policy_engine import POLICY_RULES, POLICY_SOURCES
        return {"ok": len(POLICY_RULES) > 0, "regras": len(POLICY_RULES), "programas": sorted(POLICY_SOURCES)}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:150]}


def check_wp():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    url = os.getenv("WP_URL", "").strip()
    if not url:
        return {"ok": None, "aviso": "WP_URL ausente — publicação desabilitada"}
    try:
        import requests
        r = requests.get(url.rstrip("/") + "/wp-json/", timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        return {"ok": r.status_code == 200, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    env = check_env()
    db = check_db()
    pol = check_policy()
    wp = check_wp()
    ok = db.get("ok") is True and pol.get("ok") is True
    out = {"ok": ok, "env": env, "db": db, "policy": pol, "wp": wp}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
