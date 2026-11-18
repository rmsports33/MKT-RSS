"""Proveniencia do corpo WordPress: marca e valida o pacote do motor.

A marca e um comentario HTML inserido APOS a execucao dos modulos. O Gate
WordPress compara o hash declarado com o corpo sem a marca; se nao houver
marca valida, o rascunho nao e elegivel para revisao/publicacao.
"""
import hashlib
import json
import re

PADRAO = re.compile(r"<!--\s*cxeg-package:v1:(\{[^\r\n<>]*\})\s*-->")

MODULOS_OBRIGATORIOS = (
    "editorial_identity",
    "editorial_core_offline",
    "seo",
    "editorial_readiness",
    "editorial_substance",
)


def hash_corpo(corpo):
    return hashlib.sha256(corpo.rstrip().encode("utf-8")).hexdigest()


def marcar(corpo, *, modules, voice_status, substance_status, image_rights_confirmed,
           version_sha256=""):
    """Devolve corpo com marca; o hash e calculado SEM a marca."""
    limpo = PADRAO.sub("", corpo)
    manifesto = {
        "content_sha256": hash_corpo(limpo),
        "version_sha256": version_sha256,
        "modules": {m: str(modules.get(m, "SKIPPED")) for m in MODULOS_OBRIGATORIOS},
        "voice_status": str(voice_status),
        "substance_status": str(substance_status),
        "image_rights_confirmed": bool(image_rights_confirmed),
    }
    marca = "<!-- cxeg-package:v1:" + json.dumps(manifesto, ensure_ascii=False,
                                                  separators=(",", ":")) + " -->"
    return limpo.rstrip() + "\n" + marca, manifesto


def validar(corpo):
    """Espelho local da checagem do Gate. Nao concede aprovacao alguma."""
    encontrado = PADRAO.search(corpo)
    if not encontrado:
        return {"valido": False, "motivo": "marca_ausente"}
    try:
        manifesto = json.loads(encontrado.group(1))
    except ValueError:
        return {"valido": False, "motivo": "manifesto_invalido"}
    limpo = PADRAO.sub("", corpo)
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
