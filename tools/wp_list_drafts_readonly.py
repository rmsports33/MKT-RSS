"""Lista rascunhos e pendentes do WordPress: SOMENTE LEITURA.

Nao altera status, nao publica, nao aprova e nao imprime segredo. Serve para
destravar a classificacao dos rascunhos antigos (M07) sem escrita no site.

Credenciais (nunca no chat, nunca no repositorio):
    arquivo ~/.config/conexo-os/wp-reader.env com
        WP_URL=https://conexotech.com.br
        WP_USER=<usuario do aplicativo>
        WP_APP_PASSWORD=<senha de aplicativo>
    ou as mesmas variaveis exportadas no ambiente.

Uso:
    python tools/wp_list_drafts_readonly.py --saida rascunhos.json
"""
import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SITE_PERMITIDO = "https://conexotech.com.br"
ARQUIVO_PADRAO = os.path.expanduser("~/.config/conexo-os/wp-reader.env")
CAMPOS = "id,status,date,modified,author,link,title,slug"
POR_PAGINA = 100
MAX_PAGINAS = 10


def carregar_credenciais(caminho=ARQUIVO_PADRAO):
    dados = {}
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                dados[chave.strip()] = valor.strip().strip('"').strip("'")
    for chave in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        if os.getenv(chave):
            dados[chave] = os.environ[chave].strip()
    faltando = [c for c in ("WP_URL", "WP_USER", "WP_APP_PASSWORD") if not dados.get(c)]
    if faltando:
        raise SystemExit(f"credenciais ausentes: {', '.join(faltando)} (arquivo {caminho})")
    return dados


def coletar(credenciais, paginas=MAX_PAGINAS):
    if credenciais["WP_URL"].rstrip("/") != SITE_PERMITIDO:
        raise SystemExit("WP_URL nao corresponde ao site permitido")
    auth = base64.b64encode(
        f"{credenciais['WP_USER']}:{credenciais['WP_APP_PASSWORD']}".encode("utf-8")
    ).decode("ascii")
    itens = []
    for pagina in range(1, paginas + 1):
        consulta = urllib.parse.urlencode({
            "status": "draft,pending", "per_page": POR_PAGINA,
            "page": pagina, "orderby": "modified", "order": "asc",
            "_fields": CAMPOS,
        })
        pedido = urllib.request.Request(
            f"{SITE_PERMITIDO}/wp-json/wp/v2/posts?{consulta}",
            headers={"Authorization": "Basic " + auth, "Accept": "application/json",
                     "User-Agent": "MKT-RSS-Draft-Reader/1"},
            method="GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                lote = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 400:  # pagina alem da ultima
                break
            raise SystemExit(f"WordPress recusou a leitura (HTTP {exc.code})")
        if not isinstance(lote, list) or not lote:
            break
        for post in lote:
            titulo = post.get("title")
            if isinstance(titulo, dict):
                titulo = titulo.get("rendered") or titulo.get("raw") or ""
            itens.append({
                "id": post.get("id"),
                "status": post.get("status"),
                "modified": post.get("modified") or post.get("date"),
                "author": post.get("author"),
                "slug": post.get("slug"),
                "link": post.get("link"),
                "titulo": re.sub(r"<[^>]+>", "", str(titulo or "")).strip(),
            })
        if len(lote) < POR_PAGINA:
            break
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default="rascunhos.json")
    ap.add_argument("--paginas", type=int, default=MAX_PAGINAS)
    args = ap.parse_args()
    itens = coletar(carregar_credenciais(), args.paginas)
    with open(args.saida, "w", encoding="utf-8") as saida:
        json.dump({"total": len(itens), "itens": itens}, saida, ensure_ascii=False, indent=1)
    antigos = [i for i in itens if i["modified"] and i["modified"] < "2026-11-01"]
    print(f"lidos: {len(itens)} | modificados antes de 01/11: {len(antigos)}")
    print(f"gravado em: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
