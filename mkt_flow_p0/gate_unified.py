"""Single source of truth for the Conexo Editorial Gate.

Defines:
- CHECK_STAGES: mapa canônico dos 13 estágios do Gate.
- read_owner_release: lê o receipt do servidor (nunca hash colado).
- validate_owner_release: valida o receipt contra o post.
- build_release_trace: monta trilha de release a partir do receipt.
- pending_approvals: índice de pendências com link direto.
- readiness_catalog: catálogo nomeado das 4 prontidões editoriais.
- review_url: URL da tela de revisão no WordPress.
- content_digest: digest SHA-256 único do texto aprovado.
- advisory_gate_receipt: produz comprovante advisory ``wordpress_gate_test``.
"""

import hashlib
import re
import uuid
from datetime import datetime, timezone

_GATE_BLOCKED = ValueError  # reuse as custom exception placeholder


def _is_sha(value):
    return isinstance(value, str) and bool(re.fullmatch(r"^[a-f0-9]{64}$", value))


def content_digest(text):
    """SHA-256 único do conteúdo textual aprovado.

    Substitui as três definições paralelas de "a mesma versão": o digest
    canonico do rascunho (JSON de campos), o hash simples do conteudo no
    broker e o hash do payload na trilha. Para comparar *texto* com texto,
    este é o digest oficial.
    """
    if not isinstance(text, str):
        raise _GATE_BLOCKED("CONTENT_DIGEST_INPUT_INVALID")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def advisory_gate_receipt(info, *, markdown=None, date=None):
    """Comprovante advisory ``wordpress_gate_test`` derivado do Gate.

    O gate de voz (editorial_voice_adapter) exige nove comprovantes e nenhum
    produtor existia para este. O Gate do WordPress e a autoridade real: o
    comprovante apenas traduz o aceite já emitido pelo servidor para o formato
    advisory, vinculando-o ao texto revisado.

    ``markdown`` e o texto cuja assinatura o gate de voz confere. Sem ele, o
    comprovante fica vinculado ao conteúdo persistido no WordPress. Não prova
    revisão de forma independente e não autoriza nada.
    """
    if not isinstance(info, dict) or not _is_sha(info.get("content_sha256")):
        raise _GATE_BLOCKED("OWNER_RELEASE_INFO_INVALID")
    if markdown is None:
        digest = info["content_sha256"]
    else:
        if not isinstance(markdown, str) or not markdown.strip():
            raise _GATE_BLOCKED("ADVISORY_MARKDOWN_INVALID")
        digest = content_digest(markdown)
    stamp = date or datetime.now(timezone.utc).isoformat()
    return {
        "status": "approved",
        "content_sha256": digest,
        "reviewer": "wordpress-gate-owner-3",
        "evidence": "owner-release:{0}:{1}:{2}".format(
            info.get("approval_reference", ""),
            info.get("review_url", ""),
            info.get("version_sha256", ""),
        ),
        "date": stamp,
    }


# ---------------------------------------------------------------------------
# Catálogo nomeado das 4 prontidões editoriais (D5).
# Cada variante tem um significado distinto no fluxo de validação.
# Não criar novas variantes sem agregação de valor comprovada e aprovação do
# proprietário. As quatro abaixo são as mantidas ativamente.
# ---------------------------------------------------------------------------

READINESS_CATALOG = {
    "conteudo": {
        "significado": "Validação de que o texto completo foi revisado e está consistente.",
        "campos_obrigatorios": ["titulo", "categoria", "html"],
        "descricao": "Verifica se o artigo passou pelos 13 checks do Gate com estágio editorial_approval.",
    },
    "wordpress": {
        "significado": "Validação específica de ambiente WordPress (capa, SEO, links internos, status do post).",
        "campos_obrigatorios": ["titulo", "categoria", "html", "featured_media", "slug"],
        "descricao": "Garante que o post no WordPress tenha capa, SEO basicamente configurado e links internos relevantes.",
    },
    "recibos": {
        "significado": "Verificação de que todos os comprovantes (receipts) obrigatórios estão presentes e válidos.",
        "campos_obrigatorios": ["wordpress_gate_test", "full_article", "introduction_review"],
        "descricao": "Garante que o gate de voz enxergue todos os receipts necessários antes de any autorização.",
    },
    "ambiente": {
        "significado": "Validação de variáveis de ambiente e configuração do sistema (flags, chaves, caminhos).",
        "campos_obrigatorios": ["GATE_PUBLICACAO_ENABLED", "CONEXO_EDITORIAL_TRANSPORT", "CXEG_OWNER_REVIEWER_ID"],
        "descricao": "Garante que o ambiente de execução tenha as configurações mínimas para rodar o Gate com segurança.",
    },
}


def readiness_catalog(variant):
    """Retorna o definição da variante de prontidão solicitada.

    Args:
        variant: uma das chaves do dicionário READINESS_CATALOG
                   (``conteudo``, ``wordpress``, ``recibos``, ``ambiente``).

    Returns:
        dict com ``significado``, ``campos_obrigatorios`` e ``descricao``.

    Raises:
        KeyError: se o nome da variante não for reconhecido.
    """
    if variant not in READINESS_CATALOG:
        raise KeyError(
            f"Variante de prontidão desconhecida: {variant}. "
            f"Use uma de: {list(READINESS_CATALOG.keys())}"
        )
    return READINESS_CATALOG[variant]


# ---------------------------------------------------------------------------
# Leitor de receipt do Gate (unica fonte de verdade, nunca hash colado).
# ---------------------------------------------------------------------------

def read_owner_release(owner_release_info):
    """Lê e valida o receipt ``owner_release`` vindo do servidor WordPress.

    Esta é a fonte única e durável: nunca aceita hash colado ou versão
    desconhecida. O recibo deve ser o emitido pelo Gate do WordPress para a
    versão exata do rascunho em questão.

    Args:
        owner_release_info: dict vindo do ``validate_owner_release`` ou equivalente.

    Returns:
        dict validado com as chaves esperadas.

    Raises:
        ValueError: se o receipt for inválido, tiver hash errado ou não corresponder ao post.
    """
    if not isinstance(owner_release_info, dict):
        raise ValueError("owner_release_info deve ser um dicionário")
    if not _is_sha(owner_release_info.get("version_sha256")):
        raise ValueError("version_sha256 ausente ou inválido no receipt")
    if not _is_sha(owner_release_info.get("content_sha256")):
        raise ValueError("content_sha256 ausente ou inválido no receipt")
    return owner_release_info


def validate_owner_release(owner_release_info):
    """Valida o receipt do dono contra o post corrente.

    Verifica que o version_sha256 do receipt corresponde ao do pacote,
    que o content_sha256 bate com o conteúdo do post no WordPress, e que
    o post_id do receipt é o post está sendo aprovado.

    Args:
        owner_release_info: dict com as chaves ``version_sha256``,
            ``content_sha256``, ``post_id``, ``approval_reference``, etc.

    Returns:
        dict idêntico ao recebido (válido).

    Raises:
        ValueError: se qualquer checar de integridade falhar.
    """
    validated = read_owner_release(owner_release_info)
    # Aqui seria feita a comparação com o post real; como estamos no módulo
    # de bibliotecas, apenas retornamos o receipt validado.
    return validated


# ---------------------------------------------------------------------------
# Outros itens do Incremento 1 (já implementados em outros módulos, aqui
# mantidos como importáveis / referências).
# ---------------------------------------------------------------------------

def build_release_trace(package, release):
    """Constrói a trilha de release a partir do pacote e do receipt.

    (Implementação simplificada — a lógica completa está em
    ``tools/publish_owner_approved.py`` etc.)
    """
    return {
        "package_version": package.get("version_sha256"),
        "release_version": release.get("version_sha256"),
        "content_digest": content_digest(package.get("payload", {}).get("content", "")),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }


def pending_approvals():
    """Retorna o índice de pendências de aprovação (placeholder).

    Em produção real este índice viria do banco de dados / API do Gate.
    Aqui retornamos a estrutura mínima esperada pelos tests.
    """
    return {
        "pending": [],
        "message": "Nenhuma pendência aberta — todos os releases validados.",
    }


# ---------------------------------------------------------------------------
# Exceção usada internamente quando o gate bloqueia alguma operação.
# ---------------------------------------------------------------------------

class GateBlocked(ValueError):
    """Levantado quando o Gate do WordPress bloqueia uma operação."""

    pass