"""MKTFLOW.landing_generator — landing clássica (v3.11 congelada).
Adapter sobre mkt_flow_p0.landing (escape XSS + gate PASS)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mkt_flow_p0.landing import (  # noqa: F401
    gerar_landing_page_completa,
    gerar_template_landing_page,
    slugify,
)
