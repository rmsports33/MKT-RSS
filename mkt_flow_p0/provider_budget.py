"""Orçamento e resiliência das chamadas ao provedor de IA.

Motivo (26/11/2026): o plano gratuito do Groq permite 8.000 tokens por minuto.
A cadeia editorial faz redator + revisor em segundos e estourava esse teto,
gerando 429 mesmo sem uso anormal. Este módulo espaça as chamadas, reconhece
modelos retirados do catálogo e remove o `response_format` quando o modelo
selecionado não aceita JSON forçado.

Regras:
- nunca registra corpo de resposta, prompt ou segredo;
- falha de provedor preserva o insumo e vira pendência, nunca PASS;
- espera é limitada (máximo 65 s) e injetável em testes.
"""
from __future__ import annotations

import json
import math
import os
import time

LIMITE_TPM_PADRAO = 8000
FATOR_SEGURANCA = 0.85
JANELA_SEGUNDOS = 60
MAX_ESPERA_SEGUNDOS = 65
MODELOS_FALLBACK = ("qwen/qwen3.8-27b", "openai/gpt-oss-20b")
ESCOPAS = (
    ("tokens_per_day", "tokens per day"),
    ("requests_per_day", "requests per day"),
    ("tokens_per_minute", "tokens per minute"),
    ("requests_per_minute", "requests per minute"),
)


class ProviderBudget:
    """Janela deslizante simples, com relógio e espera injetáveis."""

    def __init__(self, *, sleep=None, clock=None, limite_tpm=LIMITE_TPM_PADRAO):
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._limite = max(1, int(int(limite_tpm) * FATOR_SEGURANCA))
        self._inicio = None
        self._usados = 0
        self.espera_total = 0.0
        self.ultimo_escopo = None
        self.modelo = None

    def _renovar(self, agora):
        if self._inicio is None or agora - self._inicio >= JANELA_SEGUNDOS:
            self._inicio, self._usados = agora, 0

    def esperar(self, necessarios=0):
        agora = self._clock()
        self._renovar(agora)
        if self._usados + max(0, int(necessarios or 0)) <= self._limite:
            return 0.0
        restante = max(0.0, JANELA_SEGUNDOS - (agora - self._inicio))
        if restante:
            self._sleep(restante)
            self.espera_total += restante
        self._inicio, self._usados = self._clock(), 0
        return restante

    def registrar(self, tokens=0, *, escopo=None, retry_after=None):
        agora = self._clock()
        self._renovar(agora)
        self._usados += max(0, int(tokens or 0))
        self.ultimo_escopo = escopo
        if escopo in ("tokens_per_minute", "requests_per_minute") and retry_after is not None:
            espera = min(MAX_ESPERA_SEGUNDOS, max(0.0, float(retry_after)))
            if espera:
                self._sleep(espera)
                self.espera_total += espera
            self._inicio, self._usados = self._clock(), 0

    def status(self):
        return {
            "limite_tpm_utilizado": self._limite,
            "tokens_na_janela": self._usados,
            "espera_total_segundos": round(self.espera_total, 2),
            "ultimo_escopo": self.ultimo_escopo,
            "modelo": self.modelo,
        }


BUDGET = ProviderBudget()


def estimar_tokens(mensagens, max_tokens=0):
    """Aproximação conservadora em chars/4, sem medir prompt real."""
    try:
        corpo = json.dumps(mensagens, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        corpo = str(mensagens)
    return len(corpo) // 4 + max(0, int(max_tokens or 0))


def escopo_do_limite(exc):
    detalhe = str(exc).casefold()
    return next((nome for nome, marcador in ESCOPAS if marcador in detalhe), "unknown")


def _valor_retry_after(exc):
    try:
        cabecalhos = getattr(getattr(exc, "response", None), "headers", {}) or {}
        valor = float(cabecalhos.get("retry-after"))
    except (ValueError, TypeError, AttributeError, KeyError):
        return None
    return valor if math.isfinite(valor) and 0 <= valor <= 86400 else None


def retry_after_segundos(exc):
    """Tempo que este processo pode esperar (limite de segurança)."""
    valor = _valor_retry_after(exc)
    return math.ceil(valor) if valor is not None and valor <= MAX_ESPERA_SEGUNDOS else None


def retry_after_exportado(exc):
    """Tempo informado pelo provedor, para diagnóstico; não autoriza espera longa."""
    valor = _valor_retry_after(exc)
    return math.ceil(valor) if valor is not None else None


def codigo_do_erro(exc):
    status = getattr(exc, "status_code", None)
    if status in (401, 403):
        return "PROVIDER_AUTH"
    if status == 429 or "429" in str(exc):
        return "PROVIDER_RATE_LIMIT"
    if status in (400, 404, 422):
        return "PROVIDER_REQUEST"
    if isinstance(exc, TimeoutError) or type(exc).__name__ in {
            "APITimeoutError", "ReadTimeout", "ConnectTimeout", "TimeoutException"}:
        return "PROVIDER_TIMEOUT"
    return "PROVIDER_EXCEPTION"


def modelo_disponivel(client, preferido=None):
    """Usa o modelo pedido se existir; senão escolhe um livre atual."""
    preferido = (preferido or os.getenv("GROQ_MODEL", "") or "").strip()
    try:
        catalogo = [getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
                    for m in client.models.list().data]
        catalogo = [m for m in catalogo if isinstance(m, str) and m]
    except Exception:
        return preferido or MODELOS_FALLBACK[0]
    if preferido in catalogo:
        return preferido
    for candidato in MODELOS_FALLBACK:
        if candidato in catalogo:
            return candidato
    return preferido or (catalogo[0] if catalogo else MODELOS_FALLBACK[0])


def chamar_json(client, *, model, messages, temperature, max_tokens, timeout,
                budget=None, retry_json_fallback=True):
    """Chamada única com orçamento. Retorna {"response": ...} ou {"erro": ...}.

    Erros são sempre sanitizados: código, escopo e espera, sem corpo do provedor.
    """
    budget = budget or BUDGET
    budget.modelo = model
    budget.esperar(estimar_tokens(messages, max_tokens))
    kwargs = {
        "model": model, "messages": messages, "temperature": temperature,
        "max_tokens": max_tokens, "timeout": timeout,
        "response_format": {"type": "json_object"},
    }
    try:
        resposta = client.chat.completions.create(**kwargs)
    except Exception as exc:
        codigo = codigo_do_erro(exc)
        if codigo == "PROVIDER_RATE_LIMIT":
            escopo = escopo_do_limite(exc)
            budget.registrar(escopo=escopo, retry_after=retry_after_segundos(exc))
            return {"erro": "Limite Groq atingido (429); preservar insumos e respeitar a quota gratuita.",
                    "error_code": codigo, "limit_scope": escopo,
                    "retry_after_seconds": retry_after_exportado(exc)}
        if codigo == "PROVIDER_REQUEST" and retry_json_fallback and "json" in str(exc).casefold():
            # Modelos gpt-oss rejeitam response_format obrigatório, mas aceitam
            # JSON pedido na instrução de sistema e devolvido como texto.
            kwargs.pop("response_format", None)
            try:
                resposta = client.chat.completions.create(**kwargs)
            except Exception as exc2:
                return {"erro": "Falha Groq: provider_error (detalhes privados omitidos)",
                        "error_code": codigo_do_erro(exc2)}
        else:
            return {"erro": "Falha Groq: provider_error (detalhes privados omitidos)",
                    "error_code": codigo}
    uso = getattr(resposta, "usage", None)
    tokens = int(getattr(uso, "prompt_tokens", 0) or 0)
    tokens += int(getattr(uso, "completion_tokens", 0) or 0)
    budget.registrar(tokens)
    return {"response": resposta}
