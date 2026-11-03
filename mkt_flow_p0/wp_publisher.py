"""
mkt_flow_p0.wp_publisher — Publicação WordPress via REST API
Artigos exigem o gate editorial canônico inclusive em draft; sem fallback direto.
"""
import base64
import logging
import requests

logger = logging.getLogger("wp_publisher")

def _auth_header(user: str, app_password: str) -> str:
    token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return f"Basic {token}"


def _get_ou_criar_termo(wp_url: str, user: str, app_password: str, tipo: str, nome: str, timeout: int = 10):
    """Busca categoria/tag por nome; cria se não existir. Retorna id ou None.

    tipo: "categories" | "tags". Falha de rede → None (publica sem taxonomia).
    """
    nome = (nome or "").strip()
    if not nome:
        return None
    base = f"{wp_url}/wp-json/wp/v2/{tipo}"
    headers = {"Authorization": _auth_header(user, app_password), "User-Agent": "MKT-Flow-P0/3.6"}
    try:
        r = requests.get(base, headers=headers, params={"search": nome, "per_page": 5}, timeout=timeout)
        if r.status_code == 200:
            for item in r.json():
                if str(item.get("name", "")).lower() == nome.lower():
                    return item.get("id")
        r = requests.post(base, headers={**headers, "Content-Type": "application/json"},
                          json={"name": nome}, timeout=timeout)
        if r.status_code in (200, 201):
            return r.json().get("id")
    except Exception as e:
        logger.warning(f"WP {tipo} '{nome}' falhou: {e}")
    return None


def garantir_categoria(wp_url: str, user: str, app_password: str, nome: str, timeout: int = 10):
    return _get_ou_criar_termo((wp_url or "").rstrip("/"), user, app_password, "categories", nome, timeout)


def garantir_tag(wp_url: str, user: str, app_password: str, nome: str, timeout: int = 10):
    return _get_ou_criar_termo((wp_url or "").rstrip("/"), user, app_password, "tags", nome, timeout)


def _aplicar_rank_math(wp_url: str, user: str, app_password: str, post_id, rank_math: dict, timeout: int = 10) -> dict:
    """2º passo: grava title/description/focus no Rank Math. Falha → só aviso (post já existe)."""
    meta = {}
    if rank_math.get("title"):
        meta["rank_math_title"] = str(rank_math["title"])[:60]
    if rank_math.get("description"):
        meta["rank_math_description"] = str(rank_math["description"])[:160]
    if rank_math.get("focus"):
        meta["rank_math_focusKeyword"] = str(rank_math["focus"])
    if not meta:
        return {}
    try:
        r = requests.post(f"{wp_url}/wp-json/wp/v2/posts/{post_id}",
                          headers={"Authorization": _auth_header(user, app_password),
                                   "Content-Type": "application/json", "User-Agent": "MKT-Flow-P0/3.6"},
                          json={"meta": meta}, timeout=timeout)
        if r.status_code in (200, 201):
            return {"meta_ok": True}
        return {"meta_aviso": f"Rank Math recusou ({r.status_code}) — meta vai só no HTML"}
    except Exception as e:
        return {"meta_aviso": f"Rank Math falhou: {str(e)[:100]} — meta vai só no HTML"}


def publicar_no_wordpress(
    titulo, conteudo_html, status_validacao, wp_url, wp_user, wp_app_password,
    status_desejado="draft", categoria_ids=None, tag_ids=None, imagem_url="",
    timeout=10, slug="", rank_math=None, revisao_factual=None, *, pacote_editorial=None,
    core_root=None, actor_id=None, publication_reference=None,
):
    """Compatibilidade de chamada, sem compatibilidade de bypass.

    PASS isolado nunca autoriza rede. Texto/metadados precisam coincidir com o
    pacote revisto. Imagem já deve estar identificada por media_id no pacote;
    upload/tag/SEO posterior não pode alterar silenciosamente a versão aprovada.
    """
    if status_desejado not in {"draft", "publish"}:
        return {"erro": "status_desejado invalido; usar fluxo editorial explícito"}
    if not isinstance(pacote_editorial, dict) or not core_root:
        return {"erro": "escrita bloqueada: pacote editorial canônico obrigatório"}
    payload = pacote_editorial.get("payload", {})
    if not isinstance(payload, dict):
        return {"erro": "payload editorial inválido"}
    wp = payload.get("wordpress", {})
    if not isinstance(wp, dict):
        return {"erro": "mapeamento WordPress inválido"}
    if (titulo != payload.get("title") or conteudo_html != payload.get("content")
            or (slug and slug != payload.get("slug"))
            or (categoria_ids is not None and categoria_ids != wp.get("categories"))
            or tag_ids or imagem_url or rank_math):
        return {"erro": "escrita bloqueada: conteúdo/metadados divergem da revisão"}
    from mkt_flow_p0.editorial_transport import publish_package
    return publish_package(pacote_editorial, core_root=core_root, wp_url=wp_url,
        wp_user=wp_user, wp_password=wp_app_password, actor_id=actor_id,
        intent=status_desejado, publication_reference=publication_reference,
        timeout=timeout)


def publicar_pagina(titulo: str, conteudo_html: str, slug: str, wp_url: str, wp_user: str,
                    wp_app_password: str, timeout: int = 10) -> dict:
    """Cria ou atualiza 1 página pelo slug (idempotente — ex.: sitemap editorial).

    Sem gate de afiliado: páginas de índice não divulgam produto.
    Retorna {"page_id":..., "link":..., "atualizada":bool} ou {"erro":...}.
    """
    wp_url = (wp_url or "").rstrip("/")
    if not wp_url or not wp_user or not wp_app_password:
        return {"erro": "WP_URL/WP_USER/WP_APP_PASSWORD ausentes no .env"}
    headers = {"Authorization": _auth_header(wp_user, wp_app_password),
               "Content-Type": "application/json", "User-Agent": "MKT-Flow-P0/3.6"}
    try:
        busca = requests.get(f"{wp_url}/wp-json/wp/v2/pages",
                             headers=headers, params={"slug": slug}, timeout=timeout)
        existente = (busca.json() or [None])[0] if busca.status_code == 200 else None
    except Exception as e:
        return {"erro": f"Falha ao buscar página: {str(e)[:120]}"}
    try:
        if existente and existente.get("id"):
            resp = requests.post(f"{wp_url}/wp-json/wp/v2/pages/{existente['id']}",
                                 headers=headers,
                                 json={"title": titulo, "content": conteudo_html, "slug": slug},
                                 timeout=timeout)
            atualizada = True
        else:
            resp = requests.post(f"{wp_url}/wp-json/wp/v2/pages",
                                 headers=headers,
                                 json={"title": titulo, "content": conteudo_html, "slug": slug,
                                       "status": "publish"},
                                 timeout=timeout)
            atualizada = False
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"page_id": data.get("id"), "link": data.get("link"), "atualizada": atualizada}
        return {"erro": f"WP {resp.status_code}: {resp.text[:200]}"}
    except requests.Timeout:
        return {"erro": f"WP timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha WP: {str(e)[:150]}"}


# --- M04.17C: escrita de COMPARATIVO via MCP -------------------------------
# NOTÍCIAS usam apenas o fluxo editorial assinado. Escritas CPT legadas não
# podem contornar esse controle: o transporte MCP direto é somente leitura.
#
# Por que o comparativo NÃO pode ir pelo REST: o CPT `comparativo` é
# registrado com show_in_rest=true, mas SEM `meta` — ou seja, os campos
# _conexo_prod_*, _conexo_nota_*, _conexo_buy_* e _conexo_crit_* NÃO são
# graváveis pelo REST. Um comparativo criado por POST /wp/v2/comparativo
# nasceria sem a tabela que o single-comparativo.php renderiza. Quem escreve
# esses campos é o servidor MCP (create_comparativo), no PHP.
#
# Por que MCP e não uma chamada direta ao REST: o MCP valida os parâmetros
# (limites de 3 produtos e 6 critérios, sanitização, escopo de post_type) e
# grava os metas no mesmo passo. É o contrato já testado em produção (post
# 9649 criado como draft pelo create_review, com verificação anônima 401 e
# permalink 404).
#
# Sem dependência nova: requests já é dependência do projeto.

MCP_ENDPOINT = "/wp-json/conexo/v1/mcp/execute"


def executar_ferramenta_mcp(wp_url: str, wp_user: str, wp_app_password: str,
                             tool: str, params: dict = None,
                             timeout: int = 10) -> dict:
    """Executa uma ferramenta do MCP do ConexoTech.

    Retorna {"ok": True, "result": {...}} ou {"erro": "..."}. Nunca levanta:
    quem chama é um pipeline, e exceção aqui vira queda no meio do fluxo.
    """
    read_tools = {"ping", "site_info", "get_ficha", "validate_article", "get_best_price",
                  "suggest_internal_links", "seo_audit", "generate_schema", "list_drafts", "cxaf_schema"}
    if tool not in read_tools:
        return {"erro": "MCP direto de escrita bloqueado; usar fluxo editorial assinado"}
    wp_url = (wp_url or "").rstrip("/")
    if not wp_url or not wp_user or not wp_app_password:
        return {"erro": "WP_URL/WP_USER/WP_APP_PASSWORD ausentes no .env"}
    if not tool:
        return {"erro": "tool obrigatorio"}
    headers = {
        "Authorization": _auth_header(wp_user, wp_app_password),
        "Content-Type": "application/json",
        "User-Agent": "MKT-Flow-P0/3.6",
    }
    try:
        resp = requests.post(
            f"{wp_url}{MCP_ENDPOINT}",
            headers=headers,
            json={"tool": tool, "params": params or {}},
            timeout=timeout,
        )
    except requests.Timeout:
        return {"erro": f"MCP timeout após {timeout}s"}
    except Exception as e:
        return {"erro": f"Falha MCP: {str(e)[:200]}"}

    if resp.status_code not in (200, 201):
        return {"erro": f"MCP {resp.status_code}: {resp.text[:300]}"}
    try:
        data = resp.json()
    except Exception:
        return {"erro": f"MCP resposta nao-JSON: {resp.text[:200]}"}
    if not isinstance(data, dict):
        return {"erro": "MCP resposta inesperada (nao e' objeto)"}
    if not data.get("ok"):
        return {"erro": data.get("erro") or "MCP recusou a chamada",
                "resposta": data}
    return {"ok": True, "result": data.get("result") or {}}


def publicar_comparativo(contrato: dict, wp_url: str, wp_user: str,
                         wp_app_password: str, timeout: int = 10) -> dict:
    """Cria um COMPARATIVO como rascunho, via MCP create_comparativo.

    O contrato passa por `contrato_para_mcp`, que valida a estrutura E roda o
    gate de valor por produto (M04.17A). Contrato sem evidência por produto
    NAO chega ao WordPress: nem uma requisição é feita.

    Retorna {"post_id":..., "status":"draft", "link":...} ou {"erro":...}.
    Nunca levanta: contrato inválido vira {"erro"} com a lista de erros.
    """
    from mkt_flow_p0.comparativo_contract import ContratoInvalido, contrato_para_mcp

    try:
        params = contrato_para_mcp(contrato)
    except ContratoInvalido as erro:
        return {"erro": "contrato invalido: " + "; ".join(erro.erros),
                "erros_contrato": erro.erros,
                "avisos_contrato": erro.avisos}

    # Fail-closed na fronteira de escrita: documento inteiro no corpo é o
    # defeito que a auditoria encontrou em producao (review 9183). Melhor
    # recusar do que mandar o post inteiro.
    conteudo = str(params.get("content") or "")
    baixo = conteudo.lower()
    if "<!doctype" in baixo or "<html" in baixo or "<head" in baixo:
        return {"erro": "content com documento HTML completo: "
                        "o post receberia o documento inteiro, nao o corpo"}

    resposta = executar_ferramenta_mcp(wp_url, wp_user, wp_app_password,
                                        "create_comparativo", params, timeout)
    if resposta.get("erro"):
        return resposta

    resultado = resposta.get("result") or {}
    post_id = resultado.get("post_id")
    status = resultado.get("status")
    if not post_id:
        return {"erro": "MCP nao devolveu post_id", "resposta": resultado}
    if status != "draft":
        # O MCP fixa draft; se vier outra coisa, e' erro NAO silencioso —
        # e o post_id vai junto para o post poder ser inspecionado.
        return {"erro": f"MCP devolveu status={status!r} (esperado draft)",
                "post_id": post_id, "status": status}
    return {
        "post_id": post_id,
        "status": status,
        "link": resultado.get("edit_link"),
        "fonte": "mcp:create_comparativo",
    }

