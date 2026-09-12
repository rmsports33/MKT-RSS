"""whois_tool.robust — sanitização/validação de entrada WHOIS."""
import re
import idna

_DOMINIO_RE = re.compile(r"^(?=.{1,253}$)(?!-)([a-z0-9-]{1,63}\.)+[a-z]{2,}$")


def sanitize_and_normalize(entrada: str) -> str:
    """Lower + strip + remove esquema/caminho + IDNA."""
    s = (entrada or "").strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = s.split("/")[0].split("?")[0].split("#")[0].split(":")[0]
    try:
        s = idna.encode(s).decode()
    except Exception:
        pass
    return s


def validate_domain(dominio: str) -> dict:
    d = sanitize_and_normalize(dominio)
    if not d:
        return {"valido": False, "dominio": d, "erro": "domínio vazio"}
    if _DOMINIO_RE.match(d):
        return {"valido": True, "dominio": d}
    return {"valido": False, "dominio": d, "erro": "formato inválido"}


def detect_query_type(entrada: str) -> str:
    """domain | ip | asn | invalido."""
    s = sanitize_and_normalize(entrada)
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s):
        return "ip"
    if re.match(r"^(as)?\d+$", s):
        return "asn"
    if _DOMINIO_RE.match(s):
        return "domain"
    return "invalido"
