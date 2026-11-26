"""Lista a fila de correcao de rascunhos do WordPress: SOMENTE LEITURA.

Nao altera status, nao publica, nao aprova, nao corrige nada e nao imprime
segredo. Serve para saber o que esta parado na fila editorial de rascunhos.

Fonte oficial: GET /wp-json/conexo/v1/editorial/remediation/queue
(rota do plugin Conexo; aceita a credencial editorial limitada a correcao de
rascunhos, que e bloqueada nas rotas genericas /wp/v2/posts).

Credenciais (nunca no chat, nunca no repositorio), nesta ordem:
    1) variaveis de ambiente WP_URL, WP_USER, WP_APP_PASSWORD
    2) arquivo ~/.config/conexo-os/wp-reader.env com essas tres chaves
    3) no servidor, WP_USER=Bot.editor + ~/.config/conexo-os/wp-editorial.token

Uso:
    python tools/wp_list_drafts_readonly.py --saida fila_correcao.json
    python tools/wp_list_drafts_readonly.py --json
"""
import argparse
import base64
import collections
import json
import os
import urllib.error
import urllib.request

SITE_PERMITIDO = "https://conexotech.com.br"
ARQUIVO_PADRAO = os.path.expanduser("~/.config/conexo-os/wp-reader.env")
TOKEN_EDITORIAL = os.path.expanduser("~/.config/conexo-os/wp-editorial.token")
USUARIO_EDITORIAL = "Bot.editor"
ROTA_FILA = SITE_PERMITIDO + "/wp-json/conexo/v1/editorial/remediation/queue"


def _ler_env(caminho):
    dados = {}
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                dados[chave.strip()] = valor.strip().strip('"').strip("'")
    return dados


def carregar_credenciais(caminho=ARQUIVO_PADRAO):
    dados = _ler_env(caminho)
    for chave in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        if os.getenv(chave):
            dados[chave] = os.environ[chave].strip()
    if not dados.get("WP_APP_PASSWORD") and os.path.isfile(TOKEN_EDITORIAL):
        with open(TOKEN_EDITORIAL, encoding="utf-8") as token:
            dados["WP_APP_PASSWORD"] = token.read().strip()
        dados.setdefault("WP_USER", USUARIO_EDITORIAL)
        dados.setdefault("WP_URL", SITE_PERMITIDO)
    faltando = [c for c in ("WP_URL", "WP_USER", "WP_APP_PASSWORD") if not dados.get(c)]
    if faltando:
        raise SystemExit(f"credenciais ausentes: {', '.join(faltando)} (arquivo {caminho})")
    if dados["WP_URL"].rstrip("/") != SITE_PERMITIDO:
        raise SystemExit("WP_URL nao corresponde ao site permitido")
    return dados


def _get(url, credenciais, timeout=45):
    auth = base64.b64encode(
        f"{credenciais['WP_USER']}:{credenciais['WP_APP_PASSWORD']}".encode("utf-8")
    ).decode("ascii")
    pedido = urllib.request.Request(url, headers={
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
        "User-Agent": "MKT-RSS-Draft-Reader/1",
    }, method="GET")
    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def coletar(credenciais):
    try:
        dados = _get(ROTA_FILA, credenciais)
    except urllib.error.HTTPError as exc:
        corpo = exc.read().decode("utf-8", "replace")[:200]
        raise SystemExit(f"fila recusada (HTTP {exc.code}): {corpo}")
    if not isinstance(dados, dict) or "items" not in dados:
        raise SystemExit("resposta inesperada da fila de correcao")
    return dados


def resumir(dados):
    itens = dados.get("items") or []
    tipos = collections.Counter()
    for item in itens:
        for texto in item.get("issues") or []:
            tipos[texto.split("(")[0].strip()] += 1
    return {
        "schema": dados.get("schema"),
        "total": len(itens),
        "automatica": sum(1 for i in itens if i.get("automatic_correction_available")),
        "licenca_humana": sum(1 for i in itens if i.get("requires_human_license_review")),
        "tipos": dict(tipos.most_common()),
        "mais_antigos": [
            {"post_id": i.get("post_id"), "modified_gmt": i.get("modified_gmt"),
             "titulo": i.get("title"), "issues": len(i.get("issues") or [])}
            for i in sorted(itens, key=lambda x: str(x.get("modified_gmt") or ""))[:10]
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default="fila_correcao.json")
    ap.add_argument("--json", action="store_true", help="imprime o resumo em JSON")
    args = ap.parse_args()

    dados = coletar(carregar_credenciais())
    resumo = resumir(dados)
    with open(args.saida, "w", encoding="utf-8") as saida:
        json.dump(dados, saida, ensure_ascii=False, indent=1)

    if args.json:
        print(json.dumps(resumo, ensure_ascii=False, indent=1))
        return 0

    print(f"fila de correcao ({resumo['schema']}) — rascunhos: {resumo['total']}")
    print(f"com correcao automatica possivel: {resumo['automatica']}")
    print(f"exigem revisao humana de licenca: {resumo['licenca_humana']}")
    print("\nproblemas mais frequentes:")
    for texto, qtd in resumo["tipos"].items():
        print(f"  {qtd:>3}x  {texto}")
    print("\nrascunhos mais antigos:")
    for item in resumo["mais_antigos"]:
        print(f"  {item['post_id']:>6} | {str(item['modified_gmt'])[:10]} | "
              f"{item['issues']} problemas | {str(item['titulo'])[:60]}")
    print(f"\ndados completos: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
