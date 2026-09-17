# -*- coding: utf-8 -*-
"""links_internos.py — sugere e insere links para o arquivo do site.

SEO interno hoje = zero automatizado. Este módulo consulta a busca
pública do WordPress (/wp-json/wp/v2/search, sem chave), pontua por
sobreposição de palavras-chave e devolve os 2 melhores (excluindo a
própria página). Só leitura por padrão; aplicação é decisão do chamador.

Uso (sugestão, sem tocar no site):
    python links_internos.py --site https://conexotech.com.br \
        --titulo "Galaxy S26 Ultra: a melhor câmera" \
        --keys "galaxy,samsung,camera,smartphone" --excluir /reviews/galaxy-s26-ultra-review/

Integração no pipeline (dono/dev, 3 linhas após a reescrita):
    from links_internos import sugerir
    for l in sugerir(html_ou_titulo, keys, site, excluir_url):
        ...anexar box ou registrar para revisão...
"""
import argparse
import json
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (linkagem interna editorial; baixo volume)"}
LIMIAR = 2  # mínimo de palavras-chave em comum para sugerir


def _norm(texto):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", texto or "")
                   if not unicodedata.combining(c)).lower()


def _tokens(texto):
    return {t for t in re.split(r"\W+", _norm(texto)) if len(t) >= 3}


def buscar_candidatos(site_url, consulta, limite=20):
    """Busca pública do WP. Retorna [{id, titulo, url}]. Só GET, sem chave."""
    q = urllib.parse.urlencode({"search": consulta, "per_page": limite})
    req = urllib.request.Request(site_url.rstrip("/") + "/wp-json/wp/v2/search?" + q,
                                 headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    saida = []
    for it in data if isinstance(data, list) else []:
        if it.get("type") == "post":
            saida.append({"id": it.get("id"), "titulo": it.get("title", ""),
                          "url": it.get("url", "")})
    return saida


def pontuar(titulo_cand, keywords, excluir_url="", url_cand=""):
    """Escore = nº de keywords presentes no título. 0 se for a própria página."""
    if excluir_url and excluir_url.rstrip("/") in (url_cand or "").rstrip("/"):
        return -1
    toks = _tokens(titulo_cand)
    return sum(1 for k in keywords if _norm(k.strip()) in toks)


def sugerir(titulo_ou_html, keywords, site_url, excluir_url="", limite=2, limiar=LIMIAR):
    """Top-N {titulo, url, pontos} com pontos >= LIMIAR. Puro, sem efeito colateral."""
    if isinstance(keywords, str):
        keywords = [k for k in keywords.split(",") if k.strip()]
    texto = re.sub(r"<[^>]+>", " ", titulo_ou_html or "")
    primerias = sorted(set(re.split(r"\W+", texto.lower())))[:6]
    vistos, ranked = {}, []
    for termo in [t for t in primerias if len(t) >= 4][:3]:
        try:
            cands = buscar_candidatos(site_url, termo)
        except Exception:
            continue
        for c in cands:
            if c["url"] in vistos:
                continue
            vistos[c["url"]] = True
            pts = pontuar(c["titulo"], keywords, excluir_url, c["url"])
            if pts >= limiar:
                ranked.append({"titulo": c["titulo"], "url": c["url"], "pontos": pts})
    ranked.sort(key=lambda x: -x["pontos"])
    return ranked[:limite]


def inserir_box(html, links):
    """Anexa bloco 'Leia também' ao fim do HTML. Links reais, sem invenção."""
    if not links:
        return html
    lis = "".join('<li><a href="%s">%s</a></li>' % (l["url"], l["titulo"]) for l in links)
    return html.rstrip() + "\n<h2>Leia também</h2>\n<ul>\n%s\n</ul>\n" % lis


def main():
    ap = argparse.ArgumentParser(description="Links internos (somente leitura)")
    ap.add_argument("--site", required=True)
    ap.add_argument("--titulo", required=True)
    ap.add_argument("--keys", required=True, help="palavras separadas por vírgula")
    ap.add_argument("--excluir", default="")
    ap.add_argument("--limite", type=int, default=2)
    ap.add_argument("--limiar", type=int, default=LIMIAR,
                    help="mínimo de palavras em comum (padrão 2; use 1 em acervos pequenos)")
    a = ap.parse_args()
    print(json.dumps(sugerir(a.titulo, a.keys, a.site, a.excluir, a.limite, a.limiar),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
