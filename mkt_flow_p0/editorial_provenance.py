"""Proveniencia verificavel do corpo WordPress.

A marca comprova integridade e estado declarado do pacote. Ela NAO autentica
quem executou os modulos, quem confirmou direitos nem quem revisou o artigo.
A aprovacao humana e a autorizacao de publicacao continuam no Gate confiavel.

O consumidor deve validar o corpo bruto persistido (WordPress content.raw),
nunca confiar somente em content.rendered ou em uma marca copiada pelo cliente.
"""
import hashlib
import json
import re

PREFIXO_MARCA = "<!-- cxeg-package:v1:"
PADRAO = re.compile(r"<!--\s*cxeg-package:v1:(\{.*?\})\s*-->", re.S)
OCORRENCIA = re.compile(r"cxeg-package\s*:", re.IGNORECASE)
SHA256 = re.compile(r"^[0-9a-f]{64}$")

MODULOS_OBRIGATORIOS = (
    "editorial_identity",
    "editorial_core_offline",
    "seo",
    "editorial_readiness",
    "editorial_substance",
)
CAMPOS_MANIFESTO = {
    "content_sha256",
    "version_sha256",
    "modules",
    "voice_status",
    "substance_status",
    "image_rights_confirmed",
}
ESTADOS_VOZ = {"PROMPT_APPLIED", "HUMAN_ADAPTED", "ASSISTED_ADAPTED", "NOT_APPLIED"}
ESTADOS_SUBSTANCIA = {"PASS", "PENDING", "FAIL"}
ESTADOS_EXECUCAO = {"EXECUTED", "SKIPPED", "FAILED"}


def hash_corpo(corpo):
    if not isinstance(corpo, str):
        raise TypeError("corpo deve ser texto")
    # Canonicalizacao ASCII equivalente a PHP rtrim($body, " \\t\\n\\r").
    return hashlib.sha256(corpo.rstrip(" \t\r\n").encode("utf-8")).hexdigest()


def _contar_marcas(corpo):
    return len(OCORRENCIA.findall(corpo))


def marcar(corpo, *, modules, voice_status, substance_status,
           image_rights_confirmed, version_sha256=""):
    """Insere uma única marca; estados pendentes são registrados, nunca aprovados."""
    if not isinstance(corpo, str) or not corpo.strip():
        raise ValueError("corpo vazio para marcar")
    if not isinstance(modules, dict):
        raise ValueError("modules deve ser um dicionario")
    if not isinstance(voice_status, str) or voice_status not in ESTADOS_VOZ:
        raise ValueError("voice_status invalido")
    if not isinstance(substance_status, str) or substance_status not in ESTADOS_SUBSTANCIA:
        raise ValueError("substance_status invalido")
    if type(image_rights_confirmed) is not bool:
        raise ValueError("image_rights_confirmed deve ser booleano")
    if not isinstance(version_sha256, str) or not SHA256.fullmatch(version_sha256):
        raise ValueError("version_sha256 deve ser SHA-256 hexadecimal")
    limpo = PADRAO.sub("", corpo)
    if _contar_marcas(limpo):
        raise ValueError("marca de proveniencia malformada no corpo: remova antes de marcar")
    modulos = {}
    for nome in MODULOS_OBRIGATORIOS:
        estado = modules.get(nome, "SKIPPED")
        if not isinstance(estado, str) or estado not in ESTADOS_EXECUCAO:
            raise ValueError("estado de modulo invalido: " + nome)
        modulos[nome] = estado
    manifesto = {
        "content_sha256": hash_corpo(limpo),
        "version_sha256": version_sha256,
        "modules": modulos,
        "voice_status": voice_status,
        "substance_status": substance_status,
        "image_rights_confirmed": image_rights_confirmed,
    }
    marca = PREFIXO_MARCA + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + " -->"
    return limpo.rstrip(" \t\r\n") + "\n" + marca, manifesto


def extrair_manifesto(corpo):
    """Devolve o manifesto JSON da unica marca bem formada, senao None."""
    if not isinstance(corpo, str) or _contar_marcas(corpo) != 1:
        return None
    encontrados = list(PADRAO.finditer(corpo))
    if len(encontrados) != 1:
        return None
    try:
        manifesto = json.loads(encontrados[0].group(1))
    except (TypeError, ValueError):
        return None
    return manifesto if isinstance(manifesto, dict) else None


def validar_integridade(corpo):
    """Valida estrutura, unicidade, SHA do corpo e tipos sem aprovar estados editoriais."""
    if not isinstance(corpo, str):
        return {"valido": False, "motivo": "marca_ausente"}
    quantidade = _contar_marcas(corpo)
    if quantidade == 0:
        return {"valido": False, "motivo": "marca_ausente"}
    if quantidade > 1:
        return {"valido": False, "motivo": "marca_duplicada"}
    encontrados = list(PADRAO.finditer(corpo))
    if len(encontrados) != 1:
        return {"valido": False, "motivo": "manifesto_invalido"}
    try:
        manifesto = json.loads(encontrados[0].group(1))
    except (TypeError, ValueError):
        return {"valido": False, "motivo": "manifesto_invalido"}
    if not isinstance(manifesto, dict) or set(manifesto) != CAMPOS_MANIFESTO:
        return {"valido": False, "motivo": "manifesto_invalido"}
    if (not isinstance(manifesto.get("content_sha256"), str)
            or not SHA256.fullmatch(manifesto["content_sha256"])
            or not isinstance(manifesto.get("version_sha256"), str)
            or not SHA256.fullmatch(manifesto["version_sha256"])):
        return {"valido": False, "motivo": "manifesto_invalido"}
    modulos = manifesto.get("modules")
    if (not isinstance(modulos, dict)
            or set(modulos) != set(MODULOS_OBRIGATORIOS)
            or any(not isinstance(k, str) or k not in MODULOS_OBRIGATORIOS
                   or not isinstance(v, str) or v not in ESTADOS_EXECUCAO
                   for k, v in modulos.items())):
        return {"valido": False, "motivo": "manifesto_invalido"}
    voice_status = manifesto.get("voice_status")
    substance_status = manifesto.get("substance_status")
    if (not isinstance(voice_status, str) or voice_status not in ESTADOS_VOZ
            or not isinstance(substance_status, str) or substance_status not in ESTADOS_SUBSTANCIA
            or type(manifesto.get("image_rights_confirmed")) is not bool):
        return {"valido": False, "motivo": "manifesto_invalido"}
    marca = encontrados[0]
    limpo = corpo[:marca.start()] + corpo[marca.end():]
    if manifesto["content_sha256"] != hash_corpo(limpo):
        return {"valido": False, "motivo": "hash_divergente"}
    return {"valido": True, "manifesto": manifesto}


def validar(corpo):
    """Espelho fail-closed para Gate: integridade e requisitos editoriais."""
    integridade = validar_integridade(corpo)
    if not integridade["valido"]:
        return integridade
    manifesto = integridade["manifesto"]
    modulos = manifesto["modules"]
    faltando = [m for m in MODULOS_OBRIGATORIOS if modulos.get(m) != "EXECUTED"]
    if faltando:
        return {"valido": False, "motivo": "modulos_ausentes", "faltando": faltando}
    if manifesto["voice_status"] == "NOT_APPLIED":
        return {"valido": False, "motivo": "voz_nao_aplicada"}
    if manifesto["substance_status"] != "PASS":
        return {"valido": False, "motivo": "avaliacao_substantiva_pendente"}
    if manifesto["image_rights_confirmed"] is not True:
        return {"valido": False, "motivo": "direitos_de_imagem_pendentes"}
    return {"valido": True, "manifesto": manifesto}
