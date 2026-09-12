"""
mkt_flow_p0.policy_engine — Policy Engine determinístico
Fonte canônica: mkt_flow_p0/policies/{programa}.json (com `fonte` por regra)
Fallback: mkt_flow_p0/policy_rules.json + policy_sources.json (v3.6)
Nunca infere fato ausente. UNKNOWN nunca vira PASS.
"""
import json
import pathlib

BASE = pathlib.Path(__file__).parent

# Carrega fonte canônica (policies/*.json) se existir
def _carregar_regras():
    policies_dir = BASE / "policies"
    regras = []
    fontes = {}
    if policies_dir.exists():
        for f in sorted(policies_dir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            programa = data.get("programa", f.stem)
            fonte = data.get("source", {})
            fontes[programa] = fonte
            for r in data.get("regras", []):
                r = dict(r)
                r["programa"] = programa
                if isinstance(r.get("quando", {}), dict):
                    # converte listas de volta para set quando campo era set no doc
                    quando = {}
                    for k, v in r["quando"].items():
                        if isinstance(v, list):
                            quando[k] = set(v)
                        else:
                            quando[k] = v
                    r["quando"] = quando
                regras.append(r)
        if regras:
            return regras, fontes
    # Fallback: policy_rules.json (v3.6)
    regras = json.loads((BASE / "policy_rules.json").read_text(encoding="utf-8"))
    fontes = json.loads((BASE / "policy_sources.json").read_text(encoding="utf-8"))
    for r in regras:
        quando = r.get("quando", {})
        for k, v in list(quando.items()):
            if isinstance(v, list):
                quando[k] = set(v)
    return regras, fontes


POLICY_RULES, POLICY_SOURCES = _carregar_regras()


def _fato_satisfaz(fatos: dict, condicao: dict) -> bool:
    for chave, esperado in condicao.items():
        if chave not in fatos:
            return False
        atual = fatos[chave]
        if isinstance(esperado, set):
            if atual not in esperado:
                return False
        elif atual != esperado:
            return False
    return True


def avaliar_politica(programa: str, fatos: dict) -> dict:
    programa = (programa or "").strip().lower()
    if programa not in POLICY_SOURCES:
        return {
            "status_politica": "UNKNOWN",
            "programa": programa,
            "regras": [],
            "motivo": "Programa sem política cadastrada no Policy Engine.",
        }

    regras_aplicaveis = [r for r in POLICY_RULES if r["programa"] == programa]
    resultados = []

    for regra in regras_aplicaveis:
        if _fato_satisfaz(fatos, regra["quando"]):
            resultados.append({
                "regra_id": regra["regra_id"],
                "status": regra["resultado"],
                "evidencia": regra["evidencia"],
                "fonte": POLICY_SOURCES[programa],
                "fonte_regra": regra.get("fonte"),
            })

    if any(r["status"] == "FAIL" for r in resultados):
        status = "FAIL"
    elif any(r["status"] == "UNKNOWN" for r in resultados):
        status = "UNKNOWN"
    elif resultados:
        status = "PASS"
    else:
        status = "UNKNOWN"

    return {
        "status_politica": status,
        "programa": programa,
        "regras": resultados,
        "fonte_politica": POLICY_SOURCES[programa],
    }


def construir_contexto_politica_llm(resultado_politica: dict, max_evidencias: int = 3) -> dict:
    status = resultado_politica.get("status_politica", "UNKNOWN")
    regras = resultado_politica.get("regras", [])
    contexto = {
        "programa": resultado_politica.get("programa"),
        "status_politica": status,
        "llm_can_override": False,
    }
    if status == "FAIL":
        contexto["reason_codes"] = [r.get("regra_id") for r in regras if r.get("status") == "FAIL"][:max_evidencias]
        contexto["evidencias"] = [r.get("evidencia") for r in regras if r.get("status") == "FAIL"][:max_evidencias]
    elif status == "UNKNOWN":
        contexto["reason_codes"] = [r.get("regra_id") for r in regras if r.get("status") == "UNKNOWN"][:max_evidencias]
        contexto["evidencias"] = [r.get("evidencia") for r in regras if r.get("status") == "UNKNOWN"][:max_evidencias]
        if not contexto["evidencias"]:
            contexto["reason"] = resultado_politica.get("motivo", "Evidência insuficiente para concluir a conformidade.")
    return contexto
