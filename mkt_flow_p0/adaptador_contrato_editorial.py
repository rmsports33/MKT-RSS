"""M05.6: fronteira de compatibilidade do EditorialContract v1.0.

Usa apenas snapshots serializados do contrato do bot-redator-artigo.
Nao copia classes, nao importa o renderer legado e nao concede PASS factual.
"""
from collections.abc import Mapping
from copy import deepcopy

from mkt_flow_p0.contrato_evidencias_noticia import avaliar_evidencias


def normalizar_snapshot_editorial(payload, *, content_type="noticia"):
    """Retorna copia isolada do contrato suportado ou None (fail-closed).

    O produtor canônico usa EditorialContract.to_dict(). Aqui se aceita
    exclusivamente esse formato; instâncias e duck-typing não são convertidos
    implicitamente, evitando efeitos colaterais e ambiguidades de versão.
    """
    if not isinstance(payload, Mapping):
        return None
    if content_type != "noticia":
        return None
    if payload.get("contract_version") != "1.0":
        return None
    if payload.get("content_type") != content_type:
        return None
    try:
        snapshot = deepcopy(dict(payload))
    except (TypeError, ValueError):
        return None
    if not isinstance(snapshot.get("sources"), list):
        return None
    if not isinstance(snapshot.get("claims"), list):
        return None
    return snapshot


def avaliar_snapshot_editorial(payload):
    """Compatibilidade estrutural, nunca autorização de WordPress."""
    snapshot = normalizar_snapshot_editorial(payload)
    if snapshot is None:
        return {"veredito": "BLOQUEADO", "motivos": ["snapshot_editorial_incompativel"]}
    return avaliar_evidencias(snapshot)
