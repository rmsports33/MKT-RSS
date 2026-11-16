"""Fonte unica do Gate editorial no MKT-RSS.

Este modulo NAO autoriza publicacao. Ele le, valida e normaliza o que o Gate
do WordPress (``conexo-editorial-gate`` rc5) ja decidiu, removendo as
implementacoes duplicadas do "recibo do proprietario" e do mapa de checks.

Regras que permanecem inalteradas:

- a versao aprovada e a que o SERVIDOR emite; um hash colado nunca e a fonte;
- aprovacao exige humano ``owner_id == 3`` e ``review_mode == 'owner'``;
- nenhum check ausente, pendente ou sem evidencia real vira PASS de estagio;
- a publicacao continua exclusivamente em
  ``mkt_flow_p0.editorial_broker_transport.publish_via_broker``;
- este modulo nao escreve no WordPress, no Turso nem em qualquer estado remoto.
"""
import hashlib
import os
import re
import uuid
from datetime import datetime, timezone

# --- Decisao D1 (16/11/2026): tela unica por versao ---
# Superficie canonica de aprovacao, decidida pelo proprietario.
# ``conexo-gate-revisar-lote`` (lote) e a tela unica; ``conexo-owner-review``
# permanece como modal individual legado (nao e via de aprovacao rapida).
# Mudancas futuras requerem decisao de produto do proprietario.
DECISION_D1_SCREEN = "conexo-gate-revisar-lote"
DECISION_D1_VERSION = "1.0"
DECISION_D1_DATE = "2026-11-16"

import requests

from mkt_flow_p0.editorial_trace_gate import REQUIRED
from mkt_flow_p0.editorial_transport import SITE

_SHA = re.compile(r"[a-f0-9]{64}")

# Os treze checks reais do formulario do Gate (fonte: tools/publish_owner_approved.py
# e os testes de publicacao). A lista e unica: nao pode existir check avulso.
GATE_CHECKS = (
    "versao", "titulo", "categoria", "capa", "licenca_imagem", "fontes",
    "alegacoes", "links_internos", "seo", "html", "revisao_substantiva",
    "visual_390", "visual_1440",
)

# Mapa canonico check -> estagios da trilha do executor. Todo check precisa
# sustentar ao menos um estagio e todo estagio (exceto ``generation``, que
# observa a importacao de bytes ja existentes) precisa de ao menos um check.
# A versao anterior do mapa nao cobria ``titulo``, ``categoria`` nem ``html``,
# o que permitia marcar esses checks sem que eles bloqueassem nada.
CHECK_STAGES = {
    "fontes": ("source_review", "research"),
    "alegacoes": ("research", "factual_review"),
    "revisao_substantiva": ("style_review", "editorial_approval"),
    "seo": ("seo_review",),
    "capa": ("image_review",),
    "licenca_imagem": ("image_review",),
    "links_internos": ("internal_links",),
    "visual_390": ("render_review",),
    "visual_1440": ("render_review",),
    "html": ("render_review",),
    "versao": ("editorial_approval",),
    "titulo": ("editorial_approval",),
    "categoria": ("editorial_approval",),
}

STAGE_CHECKS = {
    stage: tuple(sorted(c for c, stages in CHECK_STAGES.items() if stage in stages))
    for stage in REQUIRED
}

# Estagio sem check: o artigo ja existe e PASS observa a importacao dos bytes
# exatos. Nao afirma geracao por IA nem execucao de modelo.
STAGES_WITHOUT_CHECK = ("generation",)

# As quatro "prontidao" historicamente espalhadas pelo repositorio, agora com
# nomes explicitos. O Gate do WordPress continua sendo a autoridade unica de
# aprovacao; estas sao diagnosticos complementares.
READINESS_VARIANTS = (
    {"id": "conteudo", "module": "mkt_flow_p0.editorial_readiness",
     "callable": "avaliar_prontidao_editorial",
     "escopo": "pacote editorial (RSS e importacao)"},
    {"id": "wordpress", "module": "editorial_wordpress_readiness",
     "callable": "validate_wordpress_readiness",
     "escopo": "post persistido no WordPress"},
    {"id": "recibos", "module": "mkt_flow_p0.editorial_voice_adapter",
     "callable": "editorial_readiness",
     "escopo": "recibos advisory do adaptador de voz"},
    {"id": "ambiente", "module": "tools.mkt_release_readiness",
     "callable": "probe",
     "escopo": "prontidao do broker e do ambiente"},
)


class GateBlocked(ValueError):
    """Bloqueio estavel e legivel; nunca carrega texto do artigo nem segredo."""


def _is_sha(value):
    return isinstance(value, str) and bool(_SHA.fullmatch(value))


def content_digest(text):
    """SHA-256 unico do conteudo textual aprovado.

    Substitui as tres definicoes paralelas de "a mesma versao": o digest
    canonico do rascunho (JSON de campos), o hash simples do conteudo no
    broker e o hash do payload na trilha. Para comparar *texto* com texto,
    este e o digest oficial.
    """
    if not isinstance(text, str):
        raise GateBlocked("CONTENT_DIGEST_INPUT_INVALID")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def advisory_gate_receipt(info, *, markdown=None, date=None):
    """Comprovante advisory ``wordpress_gate_test`` derivado do Gate.

    O gate de voz (editorial_voice_adapter) exige nove comprovantes e nenhum
    produtor existia para este. O Gate do WordPress e a autoridade real: o
    comprovante apenas traduz o aceite ja emitido pelo servidor para o formato
    advisory, vinculando-o ao texto revisado.

    ``markdown`` e o texto cuja assinatura o gate de voz confere. Sem ele, o
    comprovante fica vinculado ao conteudo persistido no WordPress. Nao prova
    revisao de forma independente e nao autoriza nada.
    """
    if not isinstance(info, dict) or not _is_sha(info.get("content_sha256")):
        raise GateBlocked("OWNER_RELEASE_INFO_INVALID")
    if markdown is None:
        digest = info["content_sha256"]
    else:
        if not isinstance(markdown, str) or not markdown.strip():
            raise GateBlocked("ADVISORY_MARKDOWN_INVALID")
        digest = content_digest(markdown)
    stamp = date or datetime.now(timezone.utc).isoformat()
    return {
        "status": "approved",
        "content_sha256": digest,
        "reviewer": "wordpress-gate-owner-3",
        "evidence": "owner-release:{0}:{1}:{2}".format(
            info.get("approval_reference", ""), info.get("review_url", ""),
            info.get("version_sha256", "")),
        "date": stamp,
    }


def review_url(post_id, site=SITE):
    """Link individual do Gate (modal legado preservado pela decisao D1).

    A tela canonica de aprovacao por versao e a de lote (``batch_review_url``).
    Este link individual continua valido como fallback, nao como via rapida.
    """
    return f"{site}/wp-admin/tools.php?page=conexo-owner-review&post_id={int(post_id)}"


def batch_review_url(site=SITE):
    """Tela canonica de aprovacao por versao (decisao D1: revisar-lote)."""
    return f"{site}/wp-admin/tools.php?page=conexo-gate-revisar-lote"


def readiness_catalog():
    """Nomeia as variantes de prontidao existentes, sem reimplementar nenhuma."""
    return [dict(variant) for variant in READINESS_VARIANTS]


def readiness_overview(*, conteudo=None, wordpress=None, recibos=None, ambiente=None):
    """Ponto de entrada unico para as quatro prontidoes.

    Cada variante e calculada pelo chamador (a assinatura delas difere) e
    apenas normalizada aqui. Nenhuma delas autoriza publicacao.
    """
    return {
        "conteudo": conteudo,
        "wordpress": wordpress,
        "recibos": recibos,
        "ambiente": ambiente,
        "publication_authorized": False,
    }


def validate_checks(checks):
    """Exige os treze checks do Gate, todos VERIFICADO e com evidencia real."""
    if not isinstance(checks, dict):
        raise GateBlocked("OWNER_CHECK_SET_INVALID")
    for name in GATE_CHECKS:
        item = checks.get(name)
        if (not isinstance(item, dict)
                or item.get("estado") != "VERIFICADO"
                or not isinstance(item.get("evidencia"), list)
                or not item["evidencia"]
                or not all(isinstance(v, str) and len(v.strip()) >= 8
                           for v in item["evidencia"])):
            raise GateBlocked("OWNER_CHECK_MISSING")
    return True


def validate_owner_release(packet, post_id=None):
    """Valida um pacote ``conexo-owner-release/1`` emitido pelo Gate.

    Retorna um resumo normalizado. Nao cria, nao altera e nao aprova nada.
    """
    payload = packet.get("payload") if isinstance(packet, dict) else None
    version = packet.get("version_sha256") if isinstance(packet, dict) else None
    if (not isinstance(packet, dict)
            or packet.get("schema") != "conexo-owner-release/1"
            or not isinstance(payload, dict)
            or payload.get("owner_id") != 3
            or payload.get("review_mode") != "owner"
            or not _is_sha(version)
            or not isinstance(payload.get("content"), str)
            or not isinstance(payload.get("approval_reference"), str)
            or not payload["approval_reference"].strip()):
        raise GateBlocked("OWNER_PACKET_INVALID")
    wordpress = payload.get("wordpress")
    wp_id = wordpress.get("post_id") if isinstance(wordpress, dict) else None
    if type(wp_id) is not int or wp_id < 1:
        raise GateBlocked("OWNER_PACKET_INVALID")
    if post_id is not None and wp_id != post_id:
        raise GateBlocked("OWNER_RELEASE_POST_MISMATCH")
    validate_checks(payload.get("checks"))
    return {
        "post_id": wp_id,
        "version_sha256": version,
        "approval_reference": payload["approval_reference"],
        "article_id": payload.get("article_id"),
        "content_sha256": hashlib.sha256(
            payload["content"].encode("utf-8")).hexdigest(),
        "review_url": review_url(wp_id),
    }


def read_owner_release(post_id, *, session=None, auth=None, timeout=15, site=SITE):
    """Le no Gate o recibo do proprietario para o post e valida-o.

    A versao vem sempre do servidor. Nao existe caminho que aceite um hash
    colado como fonte da verdade.
    """
    if type(post_id) is not int or post_id < 1:
        raise GateBlocked("OWNER_POST_ID_INVALID")
    if auth is None:
        user = os.environ.get("WP_USER")
        password = os.environ.get("WP_APP_PASSWORD")
        if not user or not password:
            raise GateBlocked("WP_SERVICE_ACCOUNT_NOT_CONFIGURED")
        auth = (user, password)
    http = session if session is not None else requests
    try:
        response = http.get(
            f"{site}/wp-json/conexo/v1/editorial/owner-release/{post_id}",
            auth=auth, timeout=timeout, allow_redirects=False)
    except Exception:
        raise GateBlocked("WP_READ_OUTCOME_UNKNOWN") from None
    if response.status_code != 200:
        raise GateBlocked("WP_READ_HTTP_REJECTED")
    try:
        packet = response.json()
    except Exception:
        raise GateBlocked("WP_READ_INVALID_JSON") from None
    if not isinstance(packet, dict):
        raise GateBlocked("WP_READ_INVALID_BODY")
    info = validate_owner_release(packet, post_id)
    info["packet"] = packet
    return info


def owner_version(post_id, *, session=None, auth=None, timeout=15, site=SITE):
    """Versao aprovada emitida pelo servidor para o post."""
    return read_owner_release(post_id, session=session, auth=auth,
                              timeout=timeout, site=site)["version_sha256"]


def content_drift(release_info, current_content):
    """True quando o conteudo persistido nao e mais o conteudo aprovado."""
    if not isinstance(current_content, str):
        return True
    current = hashlib.sha256(current_content.encode("utf-8")).hexdigest()
    return current != release_info.get("content_sha256")


def build_release_trace(packet, *, run_id=None):
    """Trilha do executor derivada do mapa canonico de checks.

    ``publication_authorized`` permanece sempre False: a trilha registra
    proveniencia, nao autorizacao.
    """
    info = validate_owner_release(packet)
    payload = packet["payload"]
    digest = info["content_sha256"]
    events = []
    for stage in REQUIRED:
        if stage in STAGES_WITHOUT_CHECK:
            module = "mkt-rss.existing-wp-draft-import"
            evidence = "existing-wp-content-sha256:" + digest
        else:
            for check in STAGE_CHECKS[stage]:
                item = payload["checks"].get(check)
                if (not isinstance(item, dict)
                        or item.get("estado") != "VERIFICADO"
                        or not isinstance(item.get("evidencia"), list)
                        or not item["evidencia"]
                        or not all(isinstance(v, str) and len(v.strip()) >= 8
                                   for v in item["evidencia"])):
                    raise GateBlocked("OWNER_CHECK_MISSING")
            module = "wordpress.owner-version-review"
            evidence = "owner-approval:" + payload["approval_reference"] + ":" + stage
        events.append({"stage": stage, "module_id": module, "status": "PASS",
                       "evidence_ref": evidence})
    return {
        "schema": "conexo-editorial-executor-events/1",
        "run_id": run_id or str(uuid.uuid4()),
        "article_id": payload.get("article_id"),
        "post_id": payload["wordpress"]["post_id"],
        "content_sha256": digest,
        "publication_authorized": False,
        "events": events,
    }


def pending_approvals(items, *, receipts=None, site=SITE):
    """Indice unico de pendencias de aceite, com o link direto do Gate.

    ``items`` recebe dicionarios com ``post_id`` e, opcionalmente, ``titulo``,
    ``estado`` e ``content_sha256`` do post atual. ``receipts`` mapeia
    ``post_id`` para o pacote ``conexo-owner-release/1`` ja lido do Gate.

    O estado nunca e inventado: sem recibo valido o item aparece como
    ``aguardando_aceite``; com recibo valido, ``aceito``; com recibo valido e
    conteudo divergente do post atual, ``obsoleto``.
    """
    rows = []
    known = receipts or {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        post_id = item.get("post_id")
        if type(post_id) is not int or post_id < 1:
            continue
        receipt = known.get(post_id)
        state = "aguardando_aceite"
        version = None
        if receipt is not None:
            try:
                info = validate_owner_release(receipt, post_id)
            except GateBlocked:
                state = "aceite_invalido"
            else:
                version = info["version_sha256"]
                current = item.get("content_sha256")
                state = "aceito"
                if isinstance(current, str) and current != info["content_sha256"]:
                    state = "obsoleto"
        rows.append({
            "post_id": post_id,
            "titulo": item.get("titulo"),
            "estado": item.get("estado"),
            "gate": state,
            "version_sha256": version,
            "review_url": review_url(post_id, site),
        })
    return rows
