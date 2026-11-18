"""Proveniencia do corpo WordPress: marca e valida o pacote do motor.

A marca e um comentario HTML inserido APOS a execucao dos modulos. O Gate
WordPress compara o hash declarado com o corpo sem a marca; se nao houver
marca valida, o rascunho nao e elegivel para revisao/publicacao.

Regras da marca:
- o corpo entrega EXATAMENTE uma marca; duas iguais tambem sao recusadas;
- qualquer segunda ocorrencia do nome do pacote seguida de dois-pontos
  (`cxeg-package:` em qualquer caixa ou espacamento, marca quebrada ou copia
  dentro do texto) conta como marca extra e e recusada;
- marca ilegivel ou incompleta e recusada como malformada;
- `marcar` recusa corpo que ja traga prefixo residual, para nao produzir um
  pacote que a propria validacao reprovaria;
- o hash cobre o corpo SEM a marca: qualquer alteracao posterior invalida.

A marca registra estado, nao aprovacao: voz nao aplicada, substancia pendente
ou direitos de imagem pendentes continuam reprovando na validacao local e no
Gate, mesmo com o hash correto.
"""
import hashlib
import json
import re

PREFIXO_MARCA = "<!-- cxeg-package:v1:"
PADRAO = re.compile(r"<!--\s*cxeg-package:v1:(\{.*?\})\s*-->", re.S)
# Nome do pacote seguido de dois-pontos, tolerante a caixa e espaco: pega a
# segunda marca mesmo quando ela imita o formato com variacao.
OCORRENCIA = re.compile(r"cxeg-package\s*:", re.IGNORECASE)

MODULOS_OBRIGATORIOS = (
    "editorial_identity",
    "editorial_core_offline",
    "seo",
    "editorial_readiness",
    "editorial_substance",
)


def hash_corpo(corpo):
    if not isinstance(corpo, str):
        raise TypeError("corpo deve ser texto")
    return hashlib.sha256(corpo.rstrip().encode("utf-8")).hexdigest()


def _contar_marcas(corpo):
    """Conta ocorrencias do nome do pacote: 0, 1 ou muitas."""
    return len(OCORRENCIA.findall(corpo))


def marcar(corpo, *, modules, voice_status, substance_status, image_rights_confirmed,
           version_sha256=""):
    """Devolve corpo com a marca unica; o hash e calculado SEM a marca.

    Idempotente: uma marca anterior e removida antes de escrever a nova.
    Corpo com prefixo residual (marca quebrada ou copia) e recusado, porque o
    resultado seria um pacote invalido.
    """
    if not isinstance(corpo, str) or not corpo.strip():
        raise ValueError("corpo vazio para marcar")
    limpo = PADRAO.sub("", corpo)
    if _contar_marcas(limpo):
        raise ValueError("marca de proveniencia malformada no corpo: "
                         "remova antes de marcar")
    manifesto = {
        "content_sha256": hash_corpo(limpo),
        "version_sha256": str(version_sha256 or ""),
        "modules": {m: str((modules or {}).get(m, "SKIPPED"))
                    for m in MODULOS_OBRIGATORIOS},
        "voice_status": str(voice_status),
        "substance_status": str(substance_status),
        "image_rights_confirmed": bool(image_rights_confirmed),
    }
    marca = PREFIXO_MARCA + json.dumps(manifesto, ensure_ascii=False,
                                       separators=(",", ":")) + " -->"
    return limpo.rstrip() + "\n" + marca, manifesto


def extrair_manifesto(corpo):
    """Manifesto declarado na unica marca bem formada, ou None."""
    if not isinstance(corpo, str) or _contar_marcas(corpo) != 1:
        return None
    encontrados = list(PADRAO.finditer(corpo))
    if len(encontrados) != 1:
        return None
    try:
        manifesto = json.loads(encontrados[0].group(1))
    except ValueError:
        return None
    return manifesto if isinstance(manifesto, dict) else None


def validar(corpo):
    """Espelho local da checagem do Gate. Nao concede aprovacao alguma."""
    if not isinstance(corpo, str):
        return {"valido": False, "motivo": "marca_ausente"}
    quantidade = _contar_marcas(corpo)
    if quantidade == 0:
        return {"valido": False, "motivo": "marca_ausente"}
    if quantidade > 1:
        # Duplicada mesmo com hashes iguais: uma marca por corpo, sem excecao.
        return {"valido": False, "motivo": "marca_duplicada"}
    encontrados = list(PADRAO.finditer(corpo))
    if len(encontrados) != 1:
        return {"valido": False, "motivo": "manifesto_invalido"}
    try:
        manifesto = json.loads(encontrados[0].group(1))
    except ValueError:
        return {"valido": False, "motivo": "manifesto_invalido"}
    if not isinstance(manifesto, dict):
        return {"valido": False, "motivo": "manifesto_invalido"}
    # Remover somente a unica marca validada. Nunca apagar silenciosamente
    # uma segunda marca ou fragmento de marca antes de conferir integridade.
    limpo = corpo[:encontrados[0].start()] + corpo[encontrados[0].end():]
    if manifesto.get("content_sha256") != hash_corpo(limpo):
        return {"valido": False, "motivo": "hash_divergente"}
    modulos = manifesto.get("modules") or {}
    faltando = [m for m in MODULOS_OBRIGATORIOS if modulos.get(m) != "EXECUTED"]
    if faltando:
        return {"valido": False, "motivo": "modulos_ausentes", "faltando": faltando}
    if manifesto.get("voice_status") == "NOT_APPLIED":
        return {"valido": False, "motivo": "voz_nao_aplicada"}
    if manifesto.get("substance_status") != "PASS":
        return {"valido": False, "motivo": "avaliacao_substantiva_pendente"}
    if not manifesto.get("image_rights_confirmed"):
        return {"valido": False, "motivo": "direitos_de_imagem_pendentes"}
    return {"valido": True, "manifesto": manifesto}
