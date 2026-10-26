"""Conservative negative-case checks for experimental previews.

Signals for blocking/manual review, not a semantic certification engine.
"""
import re

_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")
_PRICE = re.compile(r"R\$\s*\d[\d.,]*", re.I)
_DATE = re.compile(r"\b(?:20\d{2}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]20\d{2})\b")
_OWN_TEST = re.compile(r"\b(?:testamos|avaliamos em nosso laboratório|nosso teste|nossos testes|em nossa bancada)\b", re.I)
_FIELDS = ("titulo_seo", "texto_markdown", "meta_description", "slug", "tags", "json_ld")

def check_preview(source: str, fields: dict, *, conflicting_sources: bool = False) -> dict:
    issues = []
    if not isinstance(source, str) or not source.strip():
        issues.append("fonte_ausente")
    if conflicting_sources:
        issues.append("fontes_contraditorias_revisao")
    if not isinstance(fields, dict):
        fields = {}
        issues.append("campos_invalidos")
    for key in _FIELDS:
        value = fields.get(key)
        if value is None:
            continue
        if not isinstance(value, (str, list, dict)):
            issues.append(f"campo_invalido:{key}")
            continue
        import json
        text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        if _OWN_TEST.search(text):
            issues.append(f"teste_proprio_nao_comprovado:{key}")
        # A presence of a date in the source does not substantiate any price. Require
        # price and dated observation together in source, and date in final field.
        if _PRICE.search(text) and (not _DATE.search(text) or
                                    not _PRICE.search(source) or not _DATE.search(source)):
            issues.append(f"preco_sem_evidencia_datada:{key}")
        source_numbers = set(_NUMBER.findall(source))
        for number in set(_NUMBER.findall(text)):
            if number not in source_numbers:
                issues.append(f"numero_sem_fonte:{key}:{number}")
    return {"veredito": "BLOQUEADO" if issues else "REVISAO_OBRIGATORIA",
            "motivos": sorted(set(issues)), "certificacao_factual": False,
            "escreveu": False}
