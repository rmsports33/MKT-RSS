"""Cria UM rascunho privado no WordPress a partir de HTML ja gerado.

Nao publica, nao agenda, nao aprova, nao toca em SEO nativo. Depois de gravado,
o rascunho aparece no Gate para previa autenticada 390/1440 e revisao humana.

Credencial: precisa de WP_USER/WP_APP_PASSWORD com permissao de CRIAR rascunho.
A credencial atual `wp-editorial.token` e limitada a correcao (HTTP 403) e
sera recusada pelo proprio WordPress — nada sera gravado nesse caso.

Arquivo privado (fora do repositorio):
    ~/.config/conexo-os/wp-draft-writer.env
        WP_URL=https://conexotech.com.br
        WP_USER=<usuario com permissao de editor>
        WP_APP_PASSWORD=<senha de aplicativo>

Uso:
    python tools/stage_artigo_draft.py \
        --html artigos-pendentes/2026-11-17/preview/senado-claro-comodato.fragment.html \
        --titulo "Senado nao comprou iPhones..." \
        --fonte https://tecnoblog.net/noticias/... \
        --excerpt "..." --confirmar
"""
import argparse
import json
import os
import sys

for _c in (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.getcwd()):
    if os.path.isdir(os.path.join(_c, "mkt_flow_p0")):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break

from mkt_flow_p0.wp_draft_staging import stage_rss_draft  # noqa: E402

ENV_PADRAO = os.path.expanduser("~/.config/conexo-os/wp-draft-writer.env")
GATE = "https://conexotech.com.br/wp-admin/tools.php?page=conexo-gate-revisar-lote"


def credenciais(caminho):
    dados = {}
    if os.path.isfile(caminho):
        for linha in open(caminho, encoding="utf-8"):
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                dados[chave.strip()] = valor.strip().strip('"').strip("'")
    for chave in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        if os.getenv(chave):
            dados[chave] = os.environ[chave]
    faltando = [c for c in ("WP_URL", "WP_USER", "WP_APP_PASSWORD") if not dados.get(c)]
    if faltando:
        raise SystemExit(f"credenciais ausentes: {', '.join(faltando)} ({caminho})")
    return dados


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", required=True)
    ap.add_argument("--titulo", required=True)
    ap.add_argument("--fonte", required=True, help="URL da fonte original (slug estavel)")
    ap.add_argument("--excerpt", default="")
    ap.add_argument("--env", default=ENV_PADRAO)
    ap.add_argument("--confirmar", action="store_true")
    args = ap.parse_args()

    if not args.confirmar:
        raise SystemExit("sem --confirmar nada e gravado")

    html = open(args.html, encoding="utf-8").read().strip()
    if len(html) < 150:
        raise SystemExit("HTML curto demais para rascunho")

    cred = credenciais(args.env)
    resultado = stage_rss_draft(
        title=args.titulo, content=html, source_url=args.fonte,
        wp_url=cred["WP_URL"], wp_user=cred["WP_USER"],
        wp_password=cred["WP_APP_PASSWORD"],
        excerpt=args.excerpt or None,
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    if resultado.get("post_id"):
        pid = resultado["post_id"]
        print(f"\nGate: {GATE}")
        print(f"Edicao: https://conexotech.com.br/wp-admin/post.php?post={pid}&action=edit")
        print(f"Previa: https://conexotech.com.br/?p={pid}&preview=true")
    return 0 if resultado.get("post_id") else 1


if __name__ == "__main__":
    raise SystemExit(main())
