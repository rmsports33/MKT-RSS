"""Audita precos publicados no site: somente leitura (HTTP GET).

Nao escreve no WordPress, nao altera artigo, nao aprova nada. Baixa as URLs
publicas dos sitemaps, extrai pares preco/data e informa a idade da captura.

Uso:
    python tools/auditar_precos_publicados.py [--dias 30] [--limite 60]
"""
import argparse
import json
import re
import urllib.request
from datetime import date, datetime

SITE = "https://conexotech.com.br"
SITEMAPS = ("post-sitemap.xml", "review-sitemap.xml", "comparativo-sitemap.xml")
UA = {"User-Agent": "MKT-RSS-Price-Audit/1 (read-only)"}

_PRECO = re.compile(r"R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?")
_DATA_NUM = re.compile(r"captur\w*\s+em\s+(\d{2})[-/](\d{2})[-/](\d{4})", re.I)
_DATA_ISO = re.compile(r"captur\w*\s+em\s+(\d{4})-(\d{2})-(\d{2})", re.I)
_TAG = re.compile(r"<[^>]+>")


def _get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def urls_publicadas(limite):
    urls = []
    for nome in SITEMAPS:
        try:
            xml = _get(f"{SITE}/{nome}")
        except Exception as exc:
            print(f"aviso: {nome} indisponivel ({type(exc).__name__})")
            continue
        urls.extend(re.findall(r"<loc>(.*?)</loc>", xml))
        if len(urls) >= limite:
            break
    return urls[:limite]


def data_captura(texto):
    m = _DATA_NUM.search(texto)
    if m:
        d, mes, a = m.groups()
        try:
            return date(int(a), int(mes), int(d))
        except ValueError:
            return None
    m = _DATA_ISO.search(texto)
    if m:
        a, mes, d = m.groups()
        try:
            return date(int(a), int(mes), int(d))
        except ValueError:
            return None
    return None


def auditar(dias, limite):
    hoje = date.today()
    linhas = []
    for url in urls_publicadas(limite):
        try:
            html = _get(url)
        except Exception as exc:
            linhas.append({"url": url, "erro": type(exc).__name__})
            continue
        texto = _TAG.sub(" ", html)
        precos = _PRECO.findall(texto)
        quando = data_captura(texto)
        if not precos:
            continue
        idade = (hoje - quando).days if quando else None
        linhas.append({
            "url": url,
            "precos": sorted(set(precos))[:3],
            "data_captura": quando.isoformat() if quando else None,
            "idade_dias": idade,
            "situacao": ("desatualizado" if idade is not None and idade > dias
                         else "sem_data" if idade is None else "ok"),
        })
    return hoje, linhas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dias", type=int, default=30)
    ap.add_argument("--limite", type=int, default=60)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    hoje, linhas = auditar(args.dias, args.limite)
    if args.json:
        print(json.dumps({"data": hoje.isoformat(), "itens": linhas}, ensure_ascii=False, indent=1))
        return 0
    print(f"auditoria de precos — {hoje.isoformat()} (limite {args.dias} dias)")
    print(f"urls com preco: {len(linhas)}")
    for item in linhas:
        if "erro" in item:
            print(f"  ERRO        {item['url']} ({item['erro']})")
            continue
        marca = {"ok": "ok          ", "desatualizado": "DESATUALIZADO",
                 "sem_data": "SEM DATA    "}[item["situacao"]]
        idade = f"{item['idade_dias']}d" if item["idade_dias"] is not None else "-"
        print(f"  {marca} {idade:>5}  {item['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
