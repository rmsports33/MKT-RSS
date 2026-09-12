"""MKTFLOW.policy_engine — adapter determinístico (clássico, v3.11 congelado).
Delega ao núcleo mkt_flow_p0.policy_engine (fonte canônica única).
Expõe ainda listar_programas + construir_contexto_minimo_llm (legado)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mkt_flow_p0.policy_engine import (  # noqa: F401
    POLICY_RULES,
    POLICY_SOURCES,
    avaliar_politica,
    construir_contexto_politica_llm,
)


def listar_programas() -> list:
    return sorted(POLICY_SOURCES.keys())


def construir_contexto_minimo_llm(tarefa: str, fatos: dict, programa: str) -> dict:
    """Contexto mínimo p/ LLM: tarefa + fatos + decisão (sem catálogo completo)."""
    pol = avaliar_politica(programa, fatos or {})
    return {
        "task": tarefa,
        "facts": fatos or {},
        "policy": construir_contexto_politica_llm(pol),
        "decision": pol.get("status_politica"),
    }
