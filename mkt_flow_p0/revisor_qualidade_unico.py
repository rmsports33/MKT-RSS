"""Revisor Editorial Unico: avalia snapshot WordPress sem publicar nem aprovar.

Entrada: WP MCP posts_get(context=edit) + media_get + fontes e evidencias verificadas.
Nao consulta rede, nao inventa licencas nem substitui revisor humano.
A nota de prioridade 1..10 e intencionalmente independente deste parecer.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from html import unescape
from urllib.parse import urlparse

from mkt_flow_p0.gate_editorial_pos_ia import validar_saida

VERSAO = "conexo-article-quality/1"
HOST = "conexotech.com.br"
VALIDOS = {"VERIFICADO", "REPROVADO", "NAO_VERIFICADO"}
REQUIRED_CHECKS = (
    "versao", "titulo", "categoria", "capa", "licenca_imagem",
    "fontes", "alegacoes", "links_internos", "seo", "html",
    "revisao_substantiva", "visual_390", "visual_1440",
)
_RE_LINK = re.compile(r'href\s*=\s*["\x27](https?://[^"\x27]+)', re.I)
_RE_TAG = re.compile(r"<[^>]+>")


def _str(value):
    if isinstance(value, dict):
        return str(value.get("raw", value.get("rendered", "")) or "")
    return str(value or "")


def _txt(raw):
    return re.sub(r"\s+", " ", unescape(_RE_TAG.sub(" ", _str(raw)))).strip()


def _post(post):
    if isinstance(post, dict) and isinstance(post.get("data"), dict):
        return post["data"]
    return post


def _sha(post):
    # Excluir status e modified: pode-se publicar sem invalidar a revisao da versao.
    # Incluir tudo que influencia o parecer, especialmente corpo, categoria e capa.
    vals = {
        "id": post.get("id"), "title": _str(post.get("title")),
        "content": _str(post.get("content")),
        "excerpt": _str(post.get("excerpt")),
        "slug": post.get("slug"), "categories": post.get("categories"),
        "featured_media": post.get("featured_media"),
    }
    raw = json.dumps(vals, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _check(state, reason="", evidence=None):
    if state not in VALIDOS:
        raise ValueError("Estado de evidencia invalido")
    return {"estado": state, "motivo": reason, "evidencia": evidence or []}


def _evidence(evidences, name, fingerprint):
    """Um parecer humano apenas vale para a versao exata, com prova consultavel."""
    e = evidences.get(name)
    if not isinstance(e, dict):
        return _check("NAO_VERIFICADO", "evidencia_ausente")
    if e.get("fingerprint") != fingerprint:
        return _check("NAO_VERIFICADO", "evidencia_de_outra_versao")
    if not isinstance(e.get("referencias"), list) or not e["referencias"]:
        return _check("NAO_VERIFICADO", "referencias_ausentes")
    if not isinstance(e.get("reviewer"), str) or not e["reviewer"].strip():
        return _check("NAO_VERIFICADO", "revisor_ausente")
    if e.get("aprovado") is not True:
        return _check("REPROVADO", "revisao_nao_aprovada", e["referencias"])
    return _check("VERIFICADO", evidence=e["referencias"])


def avaliar_artigo(post, *, media=None, fontes=None, evidencias=None,
                   titulo_original_fonte=None, corpo_original_fonte=None):
    """Analisa rascunho real, sem fazer mutacoes. Faltas de prova falham fechado.

    fontes: [{url, verificada: bool, alegacoes: [str]}].
    evidencias: revisao_substantiva, visual_390 e visual_1440,
      com fingerprint, reviewer, aprovado e referencias.
    """
    post = _post(post)
    if not isinstance(post, dict) or type(post.get("id")) is not int:
        raise ValueError("Snapshot WordPress invalido: id ausente")
    evidencias = evidencias or {}
    fontes = fontes or []
    fingerprint = _sha(post)
    checks = {}
    checks["versao"] = _check("VERIFICADO", evidence=[fingerprint])
    title = _txt(post.get("title"))
    content = _str(post.get("content"))
    excerpt = _txt(post.get("excerpt"))
    links = _RE_LINK.findall(content)
    checks["titulo"] = _check(
        "VERIFICADO" if 20 <= len(title) <= 90 and not re.search(r"(?i)\b(titulo aqui|lorem ipsum)\b", title)
        else "REPROVADO", "titulo_ausente_ou_inadequado" if not (20 <= len(title) <= 90) else "")
    cat = post.get("categories") or []
    checks["categoria"] = _check("VERIFICADO" if isinstance(cat, list) and cat and 1 not in cat
                                 else "REPROVADO", "categoria_padrao_ou_ausente" if not cat or 1 in cat else "")
    capa_id = post.get("featured_media")
    checks["capa"] = _check("VERIFICADO" if type(capa_id) is int and capa_id > 0
                           else "REPROVADO", "sem_capa" if not capa_id else "")
    med = (media.get("data", media) if isinstance(media, dict) else {}) or {}
    desc = _txt(med.get("description"))
    alt = _txt(med.get("alt_text"))
    # Metadados com link de licença sao declaracoes, nao prova de direito.
    licenca_declarada = bool(re.search(r"https?://\S*(?:license|licen[cs]a)", desc, re.I))
    licenca_provada = _evidence(evidencias, "licenca_imagem", fingerprint)
    if med.get("id") != capa_id or not alt or not licenca_declarada:
        checks["licenca_imagem"] = _check("REPROVADO", "mídia_sem_alt_origem_ou_licenca_declarada")
    else:
        checks["licenca_imagem"] = licenca_provada
    fontes_ok = [f for f in fontes if isinstance(f, dict) and f.get("verificada") is True
                 and isinstance(f.get("url"), str) and f["url"] in links and
                 isinstance(f.get("alegacoes"), list) and f["alegacoes"]]
    checks["fontes"] = _check("VERIFICADO" if len(fontes_ok) >= 1 else "NAO_VERIFICADO",
                              "fontes_primarias_nao_evidenciadas" if not fontes_ok else "",
                              [f["url"] for f in fontes_ok])
    if corpo_original_fonte and content:
        alerta = validar_saida(_txt(corpo_original_fonte), _txt(content))
        # A numeric/style detector is not a factual verifier. Only independently
        # attested, version-bound evidence can complete this quality dimension.
        if alerta["veredito"] != "SEM_ALERTAS":
            checks["alegacoes"] = _check("REPROVADO", ",".join(alerta["motivos"]),
                                         [alerta["veredito"]])
        else:
            checks["alegacoes"] = _evidence(evidencias, "alegacoes", fingerprint)
    else:
        checks["alegacoes"] = _check("NAO_VERIFICADO", "texto_original_para_confronto_ausente")
    internos = [link for link in links if urlparse(link).hostname in (HOST, "www." + HOST)]
    # Quantidade nao basta: pertinencia precisa de revisao substantiva.
    # The DNA permits UP TO 3 genuinely related links, not a quota of 3.
    # Relevance and deliberate absence require version-bound human evidence.
    if len(set(internos)) > 3:
        checks["links_internos"] = _check("REPROVADO", "mais_de_tres_links_internos",
                                          sorted(set(internos)))
    else:
        checks["links_internos"] = _evidence(evidencias, "links_internos", fingerprint)
    slug = _str(post.get("slug"))
    checks["seo"] = _check(
        "VERIFICADO" if 20 <= len(slug) <= 100 and len(excerpt) >= 80 and
        len(content.split()) >= 250 else "NAO_VERIFICADO",
        "slug_resumo_ou_conteudo_insuficiente" if not (20 <= len(slug) <= 100 and len(excerpt) >= 80) else "")
    # Analise leve; nao faz parse DOM nem substitui verificacao visual.
    placeholders = bool(re.search(r"\[LINK AFILIADO\]|FACHADA_VIDEO|lorem ipsum", content, re.I))
    h1 = bool(re.search(r"<h1(?:\s|>)", content, re.I))
    checks["html"] = _check("REPROVADO" if placeholders or h1 else "VERIFICADO",
                             "placeholder_ou_h1_no_corpo" if placeholders or h1 else "")
    for name in ("revisao_substantiva", "visual_390", "visual_1440"):
        checks[name] = _evidence(evidencias, name, fingerprint)
    falhas = [key for key in REQUIRED_CHECKS if checks[key]["estado"] == "REPROVADO"]
    sem_prova = [key for key in REQUIRED_CHECKS if checks[key]["estado"] == "NAO_VERIFICADO"]
    veredito = ("BLOQUEADO" if falhas else
                "REVISAO_NECESSARIA" if sem_prova else
                "APTO_PARA_APROVACAO")
    return {
        "schema": VERSAO, "post_id": post["id"],
        "status_wp": post.get("status"),
        "fingerprint": fingerprint,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "veredito": veredito,
        "bloqueios": falhas, "pendencias": sem_prova,
        "prioridade_1a10_nao_equivale_a_qualidade": True,
        "publicacao_autorizada": False,
        "observacao": "Apto para aprovacao nao e autorizacao de publicacao; gate e revisor humano independentes.",
    }


def verificar_versao(parecer, post_atual):
    """Impedir uso de parecer obsoleto mesmo se WordPress modified nao mudar."""
    return bool(isinstance(parecer, dict) and
                parecer.get("schema") == VERSAO and
                parecer.get("post_id") == _post(post_atual).get("id") and
                parecer.get("fingerprint") == _sha(_post(post_atual)))
