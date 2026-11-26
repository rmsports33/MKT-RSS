"""Triagem somente leitura das pautas descobertas (Turso).

Nao decide nada: nao muda estado, nao seleciona, nao rejeita, nao escreve no
banco. Apenas classifica o que esta parado em DESCOBERTA para reduzir a leitura
humana a uma lista curta com recomendacao.

Credenciais (token de leitura):
    TURSO_DATABASE_URL + TURSO_AUTH_TOKEN no ambiente, ou
    ~/.config/conexo-os/rss-queue.env (URL) + ~/.config/conexo-os/turso-readonly.token

Uso:
    python tools/triagem_pautas_readonly.py
    python tools/triagem_pautas_readonly.py --json pautas.json
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

_CANDIDATOS = (
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.getcwd(),
)
for _candidato in _CANDIDATOS:
    if os.path.isdir(os.path.join(_candidato, "mkt_flow_p0")):
        if _candidato not in sys.path:
            sys.path.insert(0, _candidato)
        break

ENV_QUEUE = os.path.expanduser("~/.config/conexo-os/rss-queue.env")
TOKEN_READONLY = os.path.expanduser("~/.config/conexo-os/turso-readonly.token")

# Regras por URL/titulo (nao usar o resumo: ele cita outras marcas e gera falso positivo).
REGRAS = (
    ("RUMOR", ("vazamento", "rumor", "pode ter revelado", "suposto", "especula")),
    ("OFERTA", ("/achados/", "oferta", "desconto", "off", "black friday",
                "cupom", "menor pre", "preco caiu", "preço caiu")),
    ("GUIA", ("/guias/", "/responde/", "melhor ", "vale a pena", "onde roda",
              "como ", "confira")),
    ("NOTICIA", ("/noticias/",)),
)

FONTE_ESTRANGEIRA = ("gsmarena.com", "9to5", "theverge.", "engadget.")


def _alvo(pauta):
    return f"{pauta.get('titulo') or ''} {pauta.get('url') or ''}".lower()


def _classificar(pauta):
    alvo = _alvo(pauta)
    if any(fonte in alvo for fonte in FONTE_ESTRANGEIRA):
        return "FONTE_ESTRANGEIRA"
    for rotulo, chaves in REGRAS:
        if any(chave in alvo for chave in chaves):
            return rotulo
    return "OUTRO"


def _env():
    url = os.getenv("TURSO_DATABASE_URL", "").strip()
    token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
    if not url and os.path.isfile(ENV_QUEUE):
        for linha in open(ENV_QUEUE, encoding="utf-8"):
            if linha.startswith("TURSO_DATABASE_URL="):
                url = linha.split("=", 1)[1].strip()
    if not token and os.path.isfile(TOKEN_READONLY):
        token = open(TOKEN_READONLY, encoding="utf-8").read().strip()
    if not (url and token):
        raise SystemExit("faltam TURSO_DATABASE_URL e/ou token de leitura")
    os.environ["TURSO_DATABASE_URL"] = url
    os.environ["TURSO_AUTH_TOKEN"] = token


def _idade_dias(created_at):
    try:
        quando = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - quando).days


def _recomendar(pauta, categoria, idade):
    if categoria == "RUMOR":
        return "REJEITAR", "rumor sem confirmação; publicar exigiria fonte primária"
    if categoria == "FONTE_ESTRANGEIRA":
        return "REJEITAR", "fonte estrangeira em inglês; exigiria tradução e apuração própria"
    if categoria == "OFERTA":
        if idade is not None and idade > 7:
            return "REJEITAR", f"oferta de {idade} dias; o preço da matéria já mudou"
        return "SELECIONAR", "oferta recente; exige preço novo com data e link"
    if categoria == "GUIA":
        return "SELECIONAR", "guia perene; não perece com o tempo"
    if categoria == "NOTICIA":
        if idade is not None and idade > 10:
            return "REJEITAR", f"notícia de {idade} dias; perdeu atualidade"
        return "SELECIONAR", "notícia recente com fato verificável"
    return "AVALIAR", "natureza indefinida"


def coletar():
    from mkt_flow_p0.cloud_db import turso_execute
    resposta = turso_execute(
        "SELECT id, fonte, url, titulo, resumo, pontuacao, created_at "
        "FROM rss_pautas WHERE estado='DESCOBERTA' "
        "ORDER BY pontuacao DESC, created_at DESC")
    if "rows" not in resposta:
        raise SystemExit(f"leitura recusada: {json.dumps(resposta, ensure_ascii=False)[:200]}")
    itens = [dict(zip(resposta["cols"], linha)) for linha in resposta["rows"]]
    for item in itens:
        item["categoria"] = _classificar(item)
        item["idade_dias"] = _idade_dias(item.get("created_at"))
        acao, motivo = _recomendar(item, item["categoria"], item["idade_dias"])
        item["recomendacao"] = acao
        item["justificativa"] = motivo
    return itens


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", dest="json_path", default="")
    args = ap.parse_args()
    _env()
    itens = coletar()

    contagem = {}
    for item in itens:
        contagem[item["recomendacao"]] = contagem.get(item["recomendacao"], 0) + 1

    print(f"pautas em DESCOBERTA: {len(itens)} | {contagem}")
    print()
    for acao in ("SELECIONAR", "AVALIAR", "REJEITAR"):
        grupo = [i for i in itens if i["recomendacao"] == acao]
        if not grupo:
            continue
        print(f"### {acao} ({len(grupo)})")
        for item in grupo:
            idade = f"{item['idade_dias']}d" if item["idade_dias"] is not None else "?"
            print(f"  [{item['categoria']:<8} {idade:>4}] {str(item['titulo'])[:66]}")
            print(f"      {item['justificativa']}")
            print(f"      id={item['id']}")
        print()

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as saida:
            json.dump(itens, saida, ensure_ascii=False, indent=1)
        print(f"json: {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
