"""Reserva conservadora de custo do piloto; SQLite requer disco compartilhado persistente."""
import datetime
import math
import os
import sqlite3
from pathlib import Path


def reservar(custo: float) -> str:
    """Reserva o teto antes da API. Nunca libera automaticamente após erro."""
    try:
        # GitHub-hosted runners have ephemeral filesystems.\n        # A local SQLite file cannot enforce a cap across runs.\n        if os.getenv("GITHUB_ACTIONS", "").lower() == "true":\n            return "Ledger SQLite local nao e compartilhado entre GitHub Actions; chamadas reais bloqueadas"\n        limite = float(os.environ["CONEXO_CLOUD_DAILY_BUDGET_USD"])
        path = Path(os.environ["CONEXO_CLOUD_LEDGER_PATH"]).expanduser()
        if not (math.isfinite(limite) and limite > 0 and
                math.isfinite(custo) and 0 <= custo <= limite):
            return "Orcamento acumulado invalido ou excedido"
        if not path.is_absolute() or not path.parent.is_dir():
            return "Ledger persistente nao disponivel"
        dia = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        with sqlite3.connect(str(path), timeout=5, isolation_level=None) as db:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS reservas (dia TEXT PRIMARY KEY, total REAL NOT NULL)")
            anterior = db.execute("SELECT total FROM reservas WHERE dia=?", (dia,)).fetchone()
            total = float(anterior[0]) if anterior else 0.0
            if not math.isfinite(total) or total < 0 or round(total + custo, 9) > limite:
                db.execute("ROLLBACK")
                return "Orcamento diario esgotado"
            db.execute("INSERT INTO reservas(dia,total) VALUES (?,?) ON CONFLICT(dia) DO UPDATE SET total=excluded.total",
                       (dia, total + custo))
            db.execute("COMMIT")
        return ""
    except (KeyError, ValueError, OverflowError, OSError, sqlite3.Error) as exc:
        return f"Falha fechada no ledger: {type(exc).__name__}"
