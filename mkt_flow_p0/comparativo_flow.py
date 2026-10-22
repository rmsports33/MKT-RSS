"""
mkt_flow_p0.comparativo_flow — ligação operacional do redator ao WordPress
(M04.17D, 21/10/2026).

O QUE ESTE MÓDULO FAZ
---------------------
Fecha o caminho do comparativo, ponta a ponta:

    gerar_comparativo (redator)
        -> construir_contrato      (M04.17B)
        -> validar_contrato        (M04.17B, estrutural, fail-closed)
        -> avaliar_contrato        (M04.17B + gate de valor POR PRODUTO, M04.17A)
        -> publicar_comparativo    (M04.17C, MCP create_comparativo, draft)

ONDE A VALIDAÇÃO DE VALOR FICA (e por que)
-------------------------------------------
**Depois** da coleta e do enriquecimento de evidências — nunca sobre feed RSS
bruto. A medição do M04.16E mostrou que o gate ligado no caminho RSS bloqueia
7/7 feeds: num feed de terceiro não há marketplace, nem data de captura, nem
fonte primária, logo nenhum critério é satisfeito e o item inteiro é
descartado. Em comparativo, ao contrário, a evidência EXISTE e é
estruturada: o `price_history` traz preço e data por produto, e a ficha traz
a fonte. É aí que a validação tem sentido — e é aqui que ela está.

DUAS TRAVAS INDEPENDENTES
-------------------------
1. **dry-run por padrão**: `processar_comparativo` só escreve se receber
   `dry_run=False` — e o padrão é `True`. Sem dry-run, nenhuma requisição ao
   WordPress é feita.
2. **opt-in por configuração**: mesmo com `dry_run=False`, a publicação
   exige `COMPARATIVO_PUBLICACAO_ENABLED` ligada. Ausente ou com qualquer
   valor fora de {1, true, yes, on}, o fluxo devolve "desativado" e não faz
   requisição nenhuma.

O gate NÃO é flexibilizado: produto sem evidência própria é bloqueado, e o
bloqueio acontece ANTES de qualquer requisição ao WordPress.

O QUE ESTE MÓDULO NÃO FAZ
--------------------------
Não publica nada sozinho, não ativa flag nenhuma, não chama o LLM e não
coleta preço. A ORIGEM do preço é responsabilidade da coleta — e hoje ela
não existe: nem o MKT-RSS nem o redator capturam preço junto com o link do
marketplace e a data de captura (ver `auditar_precos`).
"""
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger("comparativo_flow")

_RE_URL = re.compile(r"^https?://", re.IGNORECASE)


def _eh_url(valor) -> bool:
    """Cópia local (em vez de importar um símbolo privado de outro módulo)."""
    return bool(_RE_URL.match(str(valor or "").strip()))

# Opt-in: desligado por padrão. A publication de comparativos NUNCA acontece
# so porque o codigo existe.
_ENV_OPT_IN = "COMPARATIVO_PUBLICACAO_ENABLED"
_VALORES_LIGADOS = frozenset({"1", "true", "yes", "on"})


def publicacao_ativa() -> bool:
    """True só com ativação explícita; qualquer outro valor mantém off."""
    return os.getenv(_ENV_OPT_IN, "").strip().lower() in _VALORES_LIGADOS


# --- Origem dos preços -------------------------------------------------------

def _normalizar_nome(nome: str) -> str:
    return " ".join(str(nome or "").strip().lower().split())


def auditar_precos(modelos: list, price_history: dict) -> dict:
    """Liga cada preço a SEU produto e exige origem verificável.

    Três coisas são exigidas de cada preço, por produto:
      1. **marketplace** — o link de onde o preço veio (sem ele, o preço não
         é evidência: pode ser de qualquer lugar);
      2. **data de coleta** — quando o preço foi visto (data inválida não
         conta);
      3. **vínculo inequívoco** — o preço tem que ser deste produto.

    O vínculo é por nome do produto no `price_history`; se o ponto trouxer um
    nome próprio ("produto"/"modelo"), ele tem que concordar com o nome do
    modelo — discordância é erro, não ambiguidade resolvida por aproximação.
    Preço órfão (chave sem modelo correspondente) é erro: evidência solta no
    contrato não pertence a ninguém.
    """
    nomes = [_normalizar_nome((m or {}).get("nome")) for m in (modelos or [])
             if isinstance(m, dict)]
    vinculos = []
    erros = []
    avisos = []

    for chave, pontos in (price_history or {}).items():
        nome_normalizado = _normalizar_nome(chave)
        if nome_normalizado not in nomes:
            erros.append(f"preco de '{chave}' sem produto correspondente: "
                         "evidencia solta nao pertence a ninguem")
            continue
        for ponto in (pontos or []):
            if not isinstance(ponto, dict):
                erros.append(f"preco de '{chave}' em formato invalido: {ponto!r}")
                continue
            nome_do_ponto = ponto.get("produto") or ponto.get("modelo")
            if nome_do_ponto and _normalizar_nome(nome_do_ponto) != nome_normalizado:
                erros.append(
                    f"preco de '{chave}' aponta para o produto "
                    f"{nome_do_ponto!r}: vinculo equivoco")
                continue
            fonte = ""
            for chave_fonte in ("fonte", "url", "link", "fonte_preco"):
                if _eh_url(ponto.get(chave_fonte)):
                    fonte = str(ponto.get(chave_fonte)).strip()
                    break
            if not fonte:
                avisos.append(
                    f"preco de '{chave}' sem link de marketplace: o gate nao vai "
                    "aceitar esse preco como evidencia")
            vinculos.append({
                "produto": chave,
                "preco": ponto.get("preco"),
                "data": ponto.get("data"),
                "fonte": fonte,
                "vinculo": "explicito" if nome_do_ponto else "por_nome",
            })

    return {"ok": not erros, "vinculos": vinculos, "erros": erros, "avisos": avisos}


# --- Fluxo -------------------------------------------------------------------

def processar_comparativo(
    modelos: list,
    price_history: dict = None,
    conteudo_html: str = "",
    titulo: str = "",
    categoria: str = "",
    cat_slug: str = "",
    veredito: str = "",
    notas: dict = None,
    compras: dict = None,
    criterios: list = None,
    evidencia_video: dict = None,
    evidencia_medicao: dict = None,
    wp_url: str = "",
    wp_user: str = "",
    wp_app_password: str = "",
    dry_run: bool = True,
    timeout: int = 10,
) -> dict:
    """Executa o fluxo completo do comparativo. Retorna um dicionário.

    Ações possíveis: "bloqueado", "dry_run_ok", "desativado",
    "rascunho_criado". Nunca levanta.
    """
    from mkt_flow_p0.comparativo_contract import (
        avaliar_contrato,
        construir_contrato,
        contrato_para_mcp,
        validar_contrato,
    )
    from mkt_flow_p0.wp_publisher import publicar_comparativo

    # 1) Origem dos preços: marketplace + data + vínculo inequívoco.
    auditoria = auditar_precos(modelos, price_history)
    if not auditoria["ok"]:
        return {"acao": "bloqueado", "motivo": "preco_sem_vinculo",
                "erros": auditoria["erros"], "avisos": auditoria["avisos"]}

    # 2) Contrato estruturado (M04.17B).
    try:
        contrato = construir_contrato(
            modelos=modelos, price_history=price_history,
            conteudo_html=conteudo_html, titulo=titulo, categoria=categoria,
            cat_slug=cat_slug, veredito=veredito, notas=notas, compras=compras,
            criterios=criterios, evidencia_video=evidencia_video,
            evidencia_medicao=evidencia_medicao,
        )
    except Exception as erro:  # noqa: BLE001
        return {"acao": "bloqueado", "motivo": "contrato_inexercivel",
                "erros": [str(erro)[:200]]}

    # 3) Estrutural (fail-closed).
    estrutura = validar_contrato(contrato)
    if not estrutura["ok"]:
        return {"acao": "bloqueado", "motivo": "contrato_invalido",
                "erros": estrutura["erros"], "avisos": estrutura["avisos"]}

    # 4) Gate de valor POR PRODUTO (M04.17A) + a regra do comparativo.
    avaliacao = avaliar_contrato(contrato)
    if not avaliacao["ok"]:
        return {"acao": "bloqueado", "motivo": "sem_valor_por_produto",
                "erros": avaliacao["erros"], "avisos": avaliacao["avisos"],
                "gate": avaliacao["gate"]}

    avisos = list(auditoria["avisos"]) + list(avaliacao["avisos"])

    # 5) Dry-run: mostra o plano, não escreve. Nenhuma requisição.
    if dry_run:
        try:
            plano = contrato_para_mcp(contrato)
        except Exception as erro:  # noqa: BLE001
            return {"acao": "bloqueado", "motivo": "contrato_inexercivel",
                    "erros": [str(erro)[:200]]}
        return {
            "acao": "dry_run_ok",
            "titulo": plano.get("title"),
            "produtos": plano.get("products"),
            "notas": plano.get("notas"),
            "buys": plano.get("buys"),
            "criterios": [c.get("label") for c in plano.get("crits") or []],
            "criterios_por_produto": avaliacao["gate"].get("criterios_por_produto"),
            "vinculos_preco": auditoria["vinculos"],
            "avisos": avisos,
            "escreveu": False,
            "publicacao_ativa": publicacao_ativa(),
        }

    # 6) Opt-in: sem a flag, não escreve — mesmo com dry_run=False.
    if not publicacao_ativa():
        return {"acao": "desativado", "escreveu": False,
                "motivo": f"{_ENV_OPT_IN} nao esta ligado: publicacao de "
                          "comparativos e' opt-in",
                "avisos": avisos}

    # 7) Escrita (M04.17C): rascunho via MCP, com conference de status.
    resultado = publicar_comparativo(contrato, wp_url, wp_user, wp_app_password,
                                     timeout=timeout)
    if resultado.get("erro"):
        return {"acao": "falha", "motivo": resultado.get("erro"), "erro": resultado,
                "avisos": avisos}
    return {
        "acao": "rascunho_criado",
        "post_id": resultado.get("post_id"),
        "status": resultado.get("status"),
        "link": resultado.get("link"),
        "fonte": resultado.get("fonte"),
        "escreveu": True,
        "avisos": avisos,
    }


# --- CLI ---------------------------------------------------------------------

def _main_cli(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="M04.17D — fluxo de comparativo (rascunho). Dry-run por padrão.")
    ap.add_argument("--entrada", required=True,
                    help="JSON com modelos, price_history, conteudo_html, titulo, "
                         "notas, compras, criterios")
    ap.add_argument("--aplicar", action="store_true",
                    help="escreve de verdade (exige COMPARATIVO_PUBLICACAO_ENABLED)")
    ap.add_argument("--timeout", type=int, default=10)
    args = ap.parse_args(argv)

    caminho = Path(args.entrada)
    if not caminho.is_file():
        print(json.dumps({"erro": f"arquivo nao encontrado: {caminho}"}, ensure_ascii=False))
        return 2
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as erro:  # noqa: BLE001
        print(json.dumps({"erro": f"JSON invalido: {erro}"}, ensure_ascii=False))
        return 2

    resultado = processar_comparativo(
        modelos=dados.get("modelos") or [],
        price_history=dados.get("price_history") or {},
        conteudo_html=dados.get("conteudo_html") or "",
        titulo=dados.get("titulo") or "",
        categoria=dados.get("categoria") or "",
        cat_slug=dados.get("cat_slug") or "",
        veredito=dados.get("veredito") or "",
        notas=dados.get("notas") or {},
        compras=dados.get("compras") or {},
        criterios=dados.get("criterios") or [],
        evidencia_video=dados.get("evidencia_video") or {},
        evidencia_medicao=dados.get("evidencia_medicao") or {},
        wp_url=os.getenv("WP_URL", ""),
        wp_user=os.getenv("WP_USER", ""),
        wp_app_password=os.getenv("WP_APP_PASSWORD", ""),
        dry_run=not args.aplicar,
        timeout=args.timeout,
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado.get("acao") in ("dry_run_ok", "rascunho_criado") else 1


if __name__ == "__main__":
    sys.exit(_main_cli())
