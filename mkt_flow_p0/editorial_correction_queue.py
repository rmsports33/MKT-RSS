"""Fila de correção de rascunhos antigos (Issue MKT-RSS #114).

Integração fina sobre editorial_wordpress_readiness.validate_wordpress_readiness.
A API de listagem do WordPress devolve title como objeto {"rendered": "..."},
enquanto context=edit pode devolver {"raw": "..."}. Normalizamos ambos antes
de chamar o validador canônico.

A fila é apenas diagnóstica: não escreve, aprova, publica ou agenda.
"""
import re

from editorial_wordpress_readiness import validate_wordpress_readiness

_TEST_PATTERN = re.compile(
    r"\\[\\s*(?:TESTE|TEST|NAO\\s+PUBLICAR|DO\\s+NOT\\s+PUBLISH)\\b", re.IGNORECASE)

_REASON_OWNER = {
    "featured_image_missing": "mkt_flow_p0.image_protocol",
    "uncategorized_present": "mkt_flow_p0.editorial_identity",
    "news_category_missing": "mkt_flow_p0.editorial_identity",
    "invalid_categories": "mkt_flow_p0.editorial_identity",
    "invalid_category_configuration": "config",
    "slug_missing": "mkt_flow_p0.rewriter",
    "title_missing": "mkt_flow_p0.rewriter",
    "content_missing": "mkt_flow_p0.rewriter",
    "invalid_post_link": "mkt_flow_p0.editorial_import",
    "post_id_missing": "config",
    "unexpected_status": "operador",
}


def _normalize_wordpress_list_post(post):
    """Converte o formato REST de título em string sem alterar o original."""
    normalized = dict(post)
    title = post.get("title")
    if isinstance(title, dict):
        # List context uses rendered; authenticated edit context uses raw.
        value = title.get("rendered")
        if not isinstance(value, str) or not value.strip():
            value = title.get("raw")
        normalized["title"] = value if isinstance(value, str) else ""
    elif not isinstance(title, str):
        normalized["title"] = ""
    return normalized


def classificar_rascunho(post, *, expected_category_id=10,
                         expected_site="conexotech.com.br"):
    """Classifica UM rascunho a partir de metadados de listagem."""
    if not isinstance(post, dict):
        return {"id": None, "classe": "defasado", "motivos": ["post_missing"],
                "responsaveis": [], "publicacao_autorizada": False}

    normalized = _normalize_wordpress_list_post(post)
    pid = normalized.get("id")
    titulo = normalized.get("title", "")

    if _TEST_PATTERN.search(titulo):
        return {"id": pid, "classe": "de_teste",
                "motivos": ["titulo_explicito_de_teste"],
                "responsaveis": ["operador"], "publicacao_autorizada": False}

    readiness = validate_wordpress_readiness(
        normalized, expected_category_id=expected_category_id,
        expected_site=expected_site)
    erros = list(getattr(readiness, "errors", ()) or ())
    motivos = [e for e in erros if e != "content_missing"]
    responsaveis = list(dict.fromkeys(
        _REASON_OWNER.get(e, "operador") for e in motivos))
    classe = "completo" if not motivos else "incompleto"
    return {"id": pid, "classe": classe, "motivos": motivos,
            "responsaveis": responsaveis, "publicacao_autorizada": False}


def build_correction_queue(posts, *, expected_category_id=10,
                           expected_site="conexotech.com.br"):
    """Agrega diagnósticos de uma listagem WordPress sem modificar os posts."""
    itens = [
        classificar_rascunho(post, expected_category_id=expected_category_id,
                             expected_site=expected_site)
        for post in (posts or [])
    ]
    contagens = {"completo": 0, "incompleto": 0, "de_teste": 0, "defasado": 0}
    for item in itens:
        contagens[item["classe"]] = contagens.get(item["classe"], 0) + 1
    return {
        "schema": "conexo-editorial-correction-queue/1",
        "total": len(itens), "contagens": contagens, "itens": itens,
        "publicacao_autorizada": False,
        "nota": ("Diagnóstico de metadados. Conteúdo, fatos e imagens exigem "
                 "readback autenticado e revisão humana antes de qualquer "
                 "aprovação. Itens de teste nunca devem ser publicados."),
    }
