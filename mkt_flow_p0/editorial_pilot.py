"""Executor editorial experimental fail-closed: sem WP, rede ou LLM no modo padrão.

O modo de geração aceita apenas um callback injetado pelo chamador depois da
autorização explícita, nunca importa clientes externos ou credenciais.
"""
from __future__ import annotations
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

MAX_INPUT_CHARS = 20000
MAX_TOKENS = 1200

@dataclass(frozen=True)
class Policy:
    approved: bool = False
    model: str = ""
    max_cost_usd: float = 0.0
    input_usd_per_1k: float = 0.0
    output_usd_per_1k: float = 0.0
    max_output_tokens: int = MAX_TOKENS

def _estimate_upper_bound(source: str, policy: Policy) -> float:
    # Conservador: limite superior de tokens de entrada é o número de bytes UTF-8,
    # mais 4096 tokens de folga para instruções/metadados. Não é uma conta de cobrança.
    input_bound = len(source.encode("utf-8")) + 4096
    return (input_bound * policy.input_usd_per_1k +
            policy.max_output_tokens * policy.output_usd_per_1k) / 1000

def evaluate(source: str, policy: Policy, generate: Callable[[str], dict] | None = None) -> dict:
    base = {"status": "BLOQUEADO", "verificacao_factual": "NAO_VERIFICADO",
            "escreveu": False, "wordpress": "PROIBIDO", "custo_usd_estimado": 0.0}
    if not isinstance(source, str) or not source.strip() or len(source) > MAX_INPUT_CHARS:
        return {**base, "motivo": "fonte_ausente_ou_excessiva"}
    if not policy.approved or not policy.model or generate is None:
        return {**base, "motivo": "autorizacao_ou_executor_ausente"}
    money = (policy.max_cost_usd, policy.input_usd_per_1k, policy.output_usd_per_1k)
    if (not isinstance(policy.max_output_tokens, int) or isinstance(policy.max_output_tokens, bool) or
        policy.max_output_tokens < 1 or policy.max_output_tokens > MAX_TOKENS or
        any(not isinstance(v, (int, float)) or isinstance(v, bool) or
            not math.isfinite(v) or v <= 0 for v in money)):
        return {**base, "motivo": "limites_invalidos"}
    estimated = _estimate_upper_bound(source, policy)
    if not math.isfinite(estimated) or estimated > policy.max_cost_usd:
        return {**base, "motivo": "orcamento_insuficiente",
                "teto_calculado_usd": round(estimated, 8)}
    # A callback is NOT a security sandbox: never pass untrusted/provider
    # callbacks here until process-level network and credential isolation exists.
    try:
        raw = generate(source)
    except Exception:
        return {**base, "motivo": "falha_do_executor"}
    if not isinstance(raw, dict):
        return {**base, "motivo": "saida_invalida"}
    title = raw.get("titulo_seo")
    body = raw.get("texto_markdown")
    if not isinstance(title, str) or not title.strip() or not isinstance(body, str) or not body.strip():
        return {**base, "motivo": "campos_obrigatorios_ausentes"}
    # A geração é apenas prévia: não transforma texto em certificação factual.
    return {**base, "status": "PREVIA_PENDENTE_REVISAO",
            "motivo": "certificacao_factual_pendente",
            "fonte_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "teto_calculado_usd": round(estimated, 8),
            "previsao": {"titulo_seo": title, "texto_markdown": body},
            "gerado_em_utc": datetime.now(timezone.utc).isoformat()}

def save_local(result: dict, path: Path) -> None:
    """Somente relatório de arquivo local, nunca rede/WordPress."""
    if path.suffix.lower() != ".json":
        raise ValueError("somente JSON")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def run_operational(source: str, *, approved_snapshot: bool = False,
                    generate=None) -> dict:
    """Only approved offline preview is usable as experimental operational entry.

    Backward-compatible `evaluate` remains test-only and MUST NOT be exposed to
    a network-enabled provider adapter. A callback is always denied here.
    """
    base = {"status": "BLOQUEADO", "verificacao_factual": "NAO_VERIFICADO",
            "escreveu": False, "wordpress": "PROIBIDO"}
    if generate is not None:
        return {**base, "motivo": "callback_legado_desativado"}
    from mkt_flow_p0.editorial_offline_adapter import run_offline
    return run_offline(source, approved_snapshot=approved_snapshot)
