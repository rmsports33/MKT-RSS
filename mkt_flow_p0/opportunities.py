"""Portable, offline opportunity screening. No LLM, network or publication.

Inputs are operator-supplied evidence, never factual certificates. Missing data
blocks automatic recommendation; editorial scores cannot override hard failures.
"""
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "conexo-opportunities/1"
TTL_HOURS = {"oferta": 6, "rumor": 24, "noticia": 48,
             "review": 168, "comparativo": 168, "guia": 168}


def instant(value):
    if isinstance(value, datetime):
        result = value
    else:
        try:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            result = parsedate_to_datetime(str(value))
    if result is None or result.tzinfo is None:
        raise ValueError("timestamp exige timezone: " + str(value))
    return result.astimezone(timezone.utc)


def recent(value, now, hours):
    try:
        age = (now - instant(value)).total_seconds()
        return 0 <= age <= hours * 3600
    except (ValueError, TypeError, OverflowError):
        return False


def source_url(value):
    try:
        p = urlsplit(str(value))
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def demand_report(data, now):
    """7d evidence with explicit metric. No invented volume or global threshold."""
    if not isinstance(data, dict):
        return {"status": "NAO_VERIFICADA", "reason": "DEMANDA_AUSENTE"}
    if data.get("source") not in {"trends", "search_console"}:
        return {"status": "NAO_VERIFICADA", "reason": "SUGESTAO_NAO_MEDE_DEMANDA"}
    if data.get("geo") != "BR" or not source_url(data.get("source_url")):
        return {"status": "NAO_VERIFICADA", "reason": "ORIGEM_OU_REGIAO_INVALIDA"}
    try:
        start, end = instant(data["period_start"]), instant(data["period_end"])
        fetched = instant(data["observed_at"])
        if end - start != timedelta(days=7) or not start < end <= fetched <= now:
            raise ValueError("periodo")
        # Search Console can lag; expose end and lag instead of calling it 'now'.
        if now - end > timedelta(hours=72) or not recent(fetched, now, 48):
            raise ValueError("vencido")
        points = data["points"]
        if not isinstance(points, list) or not points:
            raise ValueError("serie vazia")
        values, times = [], []
        for p in points:
            if not isinstance(p, dict):
                raise ValueError("ponto invalido")
            t, v = instant(p["at"]), p["value"]
            if not start <= t < end or p.get("partial") is True:
                raise ValueError("ponto fora ou parcial")
            if type(v) not in (float, int) or not math.isfinite(v) or v < 0:
                raise ValueError("valor")
            if data["source"] == "trends" and v > 100:
                raise ValueError("indice")
            times.append(t)
            values.append(v)
        if len(set(times)) != len(times) or times != sorted(times):
            raise ValueError("ordem ou duplicata")
        # At least one observation each day; 120-hour tail cannot pass as 7d.
        days = {int((t - start).total_seconds() // 86400) for t in times}
        if days != set(range(7)):
            raise ValueError("cobertura incompleta")
    except (KeyError, ValueError, TypeError, OverflowError):
        return {"status": "NAO_VERIFICADA", "reason": "DEMANDA_INCOMPLETA_OU_VENCIDA"}
    metric = "relative_interest" if data["source"] == "trends" else "site_impressions"
    return {"status": "SINAL_OBSERVADO" if any(values) else "SEM_SINAL_NA_AMOSTRA",
            "metric": metric, "mean": round(sum(values) / len(values), 3),
            "period_start": start.isoformat(), "period_end": end.isoformat(),
            "observed_at": fetched.isoformat(), "source": data["source"],
            "comparison_group": data.get("comparison_group"),
            "market_search_volume": None}


def evaluate(item, *, now=None):
    now = instant(now or datetime.now(timezone.utc))
    if not isinstance(item, dict) or item.get("kind") not in TTL_HOURS:
        raise ValueError("tipo de oportunidade invalido")
    if not str(item.get("title", "")).strip() or not source_url(item.get("url")):
        raise ValueError("titulo e URL HTTPS obrigatorios")
    kind, reasons, blocked = item["kind"], [], []
    if not recent(item.get("observed_at"), now, TTL_HOURS[kind]):
        reasons.append("OBSERVACAO_VENCIDA_OU_INVALIDA")
    if kind in {"noticia", "rumor"}:
        if not recent(item.get("event_at"), now, 168):
            blocked.append("FATO_FORA_DOS_7_DIAS_OU_SEM_DATA")
        if not recent(item.get("published_at"), now, TTL_HOURS[kind]):
            blocked.append("NOTICIA_PERDEU_JANELA_OU_SEM_DATA")
    else:
        products = item.get("products")
        if not isinstance(products, list) or not products:
            reasons.append("PRODUTOS_AUSENTES")
        else:
            if kind == "comparativo" and len(products) < 2:
                reasons.append("COMPARATIVO_EXIGE_PRODUTOS_DISTINTOS")
            keys = [p.get("model") for p in products if isinstance(p, dict)]
            if len(keys) != len(products) or len(set(keys)) != len(keys):
                reasons.append("IDENTIDADE_DE_PRODUTO_INVALIDA")
            for p in products:
                if not isinstance(p, dict):
                    continue
                if not p.get("model") or not p.get("variant") or p.get("market") != "BR":
                    reasons.append("VARIANTE_OU_MERCADO_NAO_CONFIRMADO")
                if not source_url(p.get("source_url")) or not recent(p.get("checked_at"), now, 168):
                    reasons.append("CICLO_COMERCIAL_SEM_EVIDENCIA_RECENTE")
                if p.get("commercial_status") in {"discontinued", "residual", "unavailable"}:
                    blocked.append("PRODUTO_FORA_DA_SELECAO_COMERCIAL")
                elif p.get("commercial_status") != "active":
                    reasons.append("CICLO_COMERCIAL_DESCONHECIDO")
                if p.get("support_status") == "ended":
                    blocked.append("SUPORTE_ENCERRADO")
                elif p.get("support_status") not in {"active", "not_applicable"}:
                    reasons.append("SUPORTE_DESCONHECIDO")
                if p.get("available_new") is not True:
                    reasons.append("DISPONIBILIDADE_NOVA_NAO_CONFIRMADA")
        if kind == "oferta":
            offer = item.get("offer", {})
            if (not recent(offer.get("checked_at"), now, 6)
                    or not source_url(offer.get("url"))
                    or offer.get("currency") != "BRL"
                    or type(offer.get("price")) not in (int, float)
                    or not math.isfinite(offer.get("price", 0)) or offer.get("price", 0) <= 0):
                reasons.append("OFERTA_SEM_PRECO_VALIDO_RECENTE")
    demand = demand_report(item.get("demand"), now)
    if demand["status"] != "SINAL_OBSERVADO":
        reasons.append(demand.get("reason", "SEM_SINAL_NA_AMOSTRA"))
    evidence = item.get("evidence", [])
    if not isinstance(evidence, list) or not evidence:
        reasons.append("EVIDENCIAS_AUSENTES")
    else:
        for e in evidence:
            if (not isinstance(e, dict) or not e.get("claim") or not e.get("locator")
                    or not source_url(e.get("source_url"))
                    or e.get("nature") not in {"official", "third_party_measurement", "editorial_inference"}
                    or not recent(e.get("checked_at"), now, 168)):
                reasons.append("EVIDENCIA_INCOMPLETA")
    return {"schema": SCHEMA, "id": hashlib.sha256(item["url"].encode()).hexdigest()[:24],
            "title": item["title"], "url": item["url"], "kind": kind,
            "status": "DESCARTAR" if blocked else ("REVISAO_PENDENTE" if reasons else "CANDIDATA_A_REVISAO"),
            "reasons": sorted(set(blocked + reasons)), "demand": demand,
            "evaluated_at": now.isoformat(), "publication_authorized": False,
            "factuality_verified": False, "own_product_test": False}


def load_candidates(path):
    path = Path(path)
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("entrada maior que 1 MiB")
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            items = list(csv.DictReader(f))
        for row in items:
            for key in ("products", "demand", "evidence", "offer"):
                if row.get(key):
                    row[key] = json.loads(row[key])
    else:
        items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError("entrada exige lista de ate 100 candidatas")
    return items
