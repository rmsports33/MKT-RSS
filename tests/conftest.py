"""conftest raiz — caminhos estáveis para toda a suíte.

Habilita importar `mkt_flow_p0`, `MKTFLOW`, `whois_tool`, `pipeline_*` de
qualquer subpasta de testes sem sys.path manual nos arquivos.
"""
import sys
from pathlib import Path

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "_legado" / "MKTFLOW", ROOT / "whois_tool", ROOT / "redator-artigo-blogs"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
# Shims para testes legados que ainda fazem `from MKTFLOW.xxx import ...`
# (Bloco C: código vivo migrou para `_legado/MKTFLOW`, import permanece compatível)
if importlib.util.find_spec("MKTFLOW") is None and (ROOT / "_legado" / "MKTFLOW").exists():
    _legado_pkg = str(ROOT / "_legado")
    if _legado_pkg not in sys.path:
        sys.path.insert(0, _legado_pkg)