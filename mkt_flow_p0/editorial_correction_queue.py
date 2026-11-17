"""Fila de correção de rascunhos antigos (Issue MKT-RSS #114).

Integration fina sobre ``editorial_wordpress_readiness.validate_wordpress_readiness``:
nao e um novo motor de validacao. Recebe metadados da listagem do WordPress
(id, status, categories, featured_media, title, slug, link — que a API DEVOLVE,
ao contrario de content) e classifica cada rascunho em:

  - `completo`     : metadados prontos para revisao humana
  - `incompleto`   : faltam metadados corrigiveis (motivo por modulo)
  - `de_teste`     : titulo explicito de teste — nunca publicar
  - `defasado`     : status inesperado ou dados divergentes

Nao escreve no WordPress, nao aprova, nao publica, nao agenda e nao fabrica
imagens/links. A fila e apenas diagnostico para o operador decidir.
"""
import re

from editorial_wordpress_readiness import validate_wordpress_readiness

_TEST_PATTERN = re.compile(
    r"\[\s*(?:TESTE|TEST|NAO\s+PUBLICAR|DO\s+NOT\s+PUBLISH)\b", re.IGNORECASE)

# Cada motivo do validador canônico -> módulo responsável pela correção.
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


def classificar_rascunho(post, *, expected_category_id=10,
                         expected_site="conexotech.com.br"):
    """Classifica UM rascunho a partir de metadados de listagem.

    Nao exige `content`: a listagem da API WordPress nao o retorna. O campo
    `content_missing` so e avaliado quando o chamador fornece o conteudo
    (ex.: readback autenticado de um post especifico).
    """
    if not isinstance(post, dict):
        return {"id": None, "classe": "defasado", "motivos": ["post_missing"],
                "responsaveis": [], "publicacao_autorizada": False}

    pid = post.get("id")
    titulo = post.get("title") if isinstance(post.get("title"), str) else ""
    if isinstance(post.get("title"), dict):  # some endpoints return {raw: ...}
        titulo = post["title"].get("raw", "")

    # Testes primeiro: nunca entram na fila de revisao normal.
    if _TEST_PATTERN.search(titulo):
        return {"id": pid, "classe": "de_teste",
                "motivos": ["titulo_explicito_de_teste"],
                "responsaveis": ["operador"], "publicacao_autorizada": False}

    readiness = validate_wordpress_readiness(
        post, expected_category_id=expected_category_id,
        expected_site=expected_site)
    erros = list(getattr(readiness, "errors", ()) or ())

    # Sem content na listagem, nao e falta real — o chamador acrescenta depois.
    motivos = [e for e in erros if e != "content_missing"]
    responsaveis = list(dict.fromkeys(
        _REASON_OWNER.get(e, "operador") for e in motivos))

    classe = "completo" if not motivos else "incompleto"
    return {
        "id": pid,
        "classe": classe,
        "motivos": motivos,
        "responsaveis": responsaveis,
        "publicacao_autorizada": False,
    }


def build_correction_queue(posts, *, expected_category_id=10,
                           expected_site="conexotech.com.br"):
    """Monta a fila de correcao a partir de uma lista de metadados de rascunhos.

    `posts` e a lista devolvida por GET /wp/v2/posts?status=draft,pending
    (sem content). Nenhum item e alterado; o resultado agrega contagens por
    classe e a lista detalhada para o operador decidir.
    """
    itens = []
    for post in posts or []:
        item = classificar_rascunho(
            post, expected_category_id=expected_category_id,
            expected_site=expected_site)
        itens.append(item)

    contagens = {"completo": 0, "incompleto": 0, "de_teste": 0, "defasado": 0}
    for item in itens:
        contagens[item["classe"]] = contagens.get(item["classe"], 0) + 1

    return {
        "schema": "conexo-editorial-correction-queue/1",
        "total": len(itens),
        "contagens": contagens,
        "itens": itens,
        "publicacao_autorizada": False,
        "nota": ("Diagnostico a partir de metadados de listagem. Conteudo/fatos/"
                 "imagens exigem readback autenticado e revisao humana antes de "
                 "qualquer aprovacao. Itens de teste nunca devem ser publicados."),
    }
