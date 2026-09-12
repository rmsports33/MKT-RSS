"""whois_tool.parser — parse de resposta WHOIS bruta em dict."""
import re


def parse_whois(raw: str) -> dict:
    """Extrai campos comuns (domain, registrar, creation/expiry, status, nameservers)."""
    raw = raw or ""
    out = {"domain": "", "registrar": "", "creation_date": "", "expiry_date": "",
           "status": [], "nameservers": [], "raw_len": len(raw)}
    m = re.search(r"(?im)^domain name:\s*(\S+)", raw)
    if m:
        out["domain"] = m.group(1).lower()
    m = re.search(r"(?im)^registrar:\s*(.+)$", raw)
    if m:
        out["registrar"] = m.group(1).strip()
    m = re.search(r"(?im)^creation date:\s*(.+)$", raw)
    if m:
        out["creation_date"] = m.group(1).strip()
    m = re.search(r"(?im)^(registry expiry date|expiry date):\s*(.+)$", raw)
    if m:
        out["expiry_date"] = m.group(2).strip()
    out["status"] = [s.strip() for s in re.findall(r"(?im)^domain status:\s*(.+)$", raw)]
    out["nameservers"] = [s.strip().lower() for s in re.findall(r"(?im)^name server:\s*(\S+)", raw)]
    return out
