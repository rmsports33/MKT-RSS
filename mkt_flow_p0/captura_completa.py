"""Cria capturas completas e auditáveis para a ponte Work, sem rede ou LLM.

A origem de dados deve ser um extrator/revisor externo: hashes atestam
integridade do snapshot, não autenticidade ou aprovação editorial.
"""
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse


def criar_captura_completa(url, texto, *, titulo, capturado_em=None, minimo_palavras=100):
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("URL da fonte inválida")
    if not isinstance(titulo, str) or not titulo.strip():
        raise ValueError("Título da fonte ausente")
    if not isinstance(texto, str) or len(texto.split()) < minimo_palavras:
        raise ValueError("Corpo da fonte incompleto")
    if not isinstance(minimo_palavras, int) or minimo_palavras < 100:
        raise ValueError("Limite de palavras inválido")
    stamp = capturado_em or datetime.now(timezone.utc).isoformat()
    if not isinstance(stamp, str) or not stamp.strip():
        raise ValueError("Data de captura inválida")
    return {
        "url": url, "titulo": titulo.strip(), "texto": texto,
        "capturado_em": stamp, "palavras": len(texto.split()),
        "sha256_texto": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
        "status_revisao": "PENDENTE",
    }


def verificar_captura_completa(captura):
    if not isinstance(captura, dict):
        return False
    texto = captura.get("texto")
    if not isinstance(texto, str) or len(texto.split()) < 100:
        return False
    try:
        url = urlparse(captura["url"])
        return (url.scheme == "https" and bool(url.netloc)
                and isinstance(captura.get("titulo"), str)
                and bool(captura["titulo"].strip())
                and isinstance(captura.get("capturado_em"), str)
                and bool(captura["capturado_em"].strip())
                and captura.get("palavras") == len(texto.split())
                and captura.get("sha256_texto") ==
                hashlib.sha256(texto.encode("utf-8")).hexdigest())
    except (KeyError, TypeError, ValueError):
        return False
