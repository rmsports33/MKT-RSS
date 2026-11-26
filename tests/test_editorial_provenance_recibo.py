"""Verificação de reprodução do recibo de proveniência. Offline."""
from mkt_flow_p0 import editorial_provenance as p

MODS = {m: "EXECUTED" for m in p.MODULOS_OBRIGATORIOS}


def test_recibo_reproduzivel():
    corpo, _ = p.marcar(
        "<p>Texto</p>", modules=MODS, voice_status="PROMPT_APPLIED",
        substance_status="PASS", image_rights_confirmed=True,
        version_sha256="a" * 64)
    out = p.verificar_recibo(corpo)
    assert out["reproduzivel"] is True
    assert out["hash_confere"] is True


def test_corpo_alterado_invalida_recibo():
    corpo, _ = p.marcar(
        "<p>Texto</p>", modules=MODS, voice_status="PROMPT_APPLIED",
        substance_status="PASS", image_rights_confirmed=True)
    alterado = corpo.replace("<p>Texto</p>", "<p>Texto mudado</p>")
    out = p.verificar_recibo(alterado)
    assert out["hash_confere"] is False
    assert out["reproduzivel"] is False


def test_sem_marca():
    out = p.verificar_recibo("<p>sem marca</p>")
    assert out["reproduzivel"] is False
    assert out["motivo"] == "marca_ausente"


def test_validar_continua_recusando_voz_nao_aplicada():
    corpo, _ = p.marcar(
        "<p>Texto</p>", modules=MODS, voice_status="NOT_APPLIED",
        substance_status="PENDING", image_rights_confirmed=False)
    assert p.validar(corpo)["valido"] is False
    assert p.verificar_recibo(corpo)["reproduzivel"] is True
