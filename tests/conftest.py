"""conftest raiz — caminhos estáveis para toda a suíte.

Habilita importar `mkt_flow_p0`, `MKTFLOW`, `whois_tool`, `pipeline_*` de
qualquer subpasta de testes sem sys.path manual nos arquivos.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "MKTFLOW", ROOT / "whois_tool", ROOT / "redator-artigo-blogs"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)