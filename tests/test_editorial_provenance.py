"""Testes da marca de proveniencia: hash, idempotencia e reprovacao conservadora."""
import json

import pytest

from mkt_flow_p0 import editorial_provenance as pv

CORPO = "<h2>Seção</h2>\n<p>Conteúdo editorial verificável.</p>"
MODULOS = {m: "EXECUTED" for m in pv.MODULOS_OBRIGATORIOS}


def marcar(corpo=CORPO, **opcoes):
    base = dict(modules=MODULOS, voice_status="ASSISTED_ADAPTED",
                substance_status="PASS", image_rights_confirmed=True,
                version_sha256="a" * 64)
    base.update(opcoes)
    return pv.marcar(corpo, **base)


def test_marca_valida_e_hash_do_corpo_sem_marca():
    corpo, manifesto = marcar()
    assert pv.validar(corpo) == {"valido": True, "manifesto": manifesto}
    assert manifesto["content_sha256"] == pv.hash_corpo(CORPO)
    assert manifesto["modules"] == MODULOS
    assert "cxeg-package:v1" in corpo


def test_marcar_e_idempotente():
    corpo, primeiro = marcar()
    repetido, segundo = marcar(corpo)
    assert repetido.count("cxeg-package") == 1
    assert repetido == corpo
    assert primeiro == segundo
    assert pv.validar(repetido)["valido"] is True


def test_hash_ignora_espacos_finais():
    assert pv.hash_corpo("abc\n\n  \n") == pv.hash_corpo("abc")


def test_adulteracao_do_corpo_invalida_a_marca():
    corpo, _ = marcar()
    alterado = corpo.replace("verificável", "adulterado")
    assert pv.validar(alterado) == {"valido": False, "motivo": "hash_divergente"}


def test_marca_ausente():
    assert pv.validar(CORPO) == {"valido": False, "motivo": "marca_ausente"}


def test_manifesto_invalido():
    quebrado = "<!-- cxeg-package:v1:{nao-e-json} -->"
    assert pv.validar(quebrado) == {"valido": False, "motivo": "manifesto_invalido"}


def test_modulo_obrigatorio_ausente():
    corpo, _ = marcar()
    manifesto = pv.extrair_manifesto(corpo)
    del manifesto["modules"]["editorial_substance"]
    adulterado = pv.PADRAO.sub("", corpo).rstrip() + "\n<!-- cxeg-package:v1:" + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + " -->"
    resultado = pv.validar(adulterado)
    assert resultado["motivo"] == "modulos_ausentes"
    assert resultado["faltando"] == ["editorial_substance"]


def test_marca_tolera_maior_que_no_manifesto():
    corpo, _ = marcar(version_sha256="v>1")
    assert pv.validar(corpo)["valido"] is True


@pytest.mark.parametrize("opcoes,motivo", [
    ({"voice_status": "NOT_APPLIED"}, "voz_nao_aplicada"),
    ({"substance_status": "PENDING"}, "avaliacao_substantiva_pendente"),
    ({"substance_status": "FAIL"}, "avaliacao_substantiva_pendente"),
    ({"image_rights_confirmed": False}, "direitos_de_imagem_pendentes"),
])
def test_reprovacao_conservadora_mesmo_com_hash_correto(opcoes, motivo):
    corpo, manifesto = marcar(**opcoes)
    assert pv.validar(corpo) == {"valido": False, "motivo": motivo}
    # O hash continua correto: a marca registra estado, nao aprova.
    assert pv.hash_corpo(pv.PADRAO.sub("", corpo)) == manifesto["content_sha256"]


def test_marcar_rejeita_corpo_vazio():
    with pytest.raises(ValueError):
        marcar(corpo="   ")


def test_extrair_manifesto_le_a_marca_declarada():
    corpo, manifesto = marcar()
    assert pv.extrair_manifesto(corpo) == manifesto
    assert pv.extrair_manifesto(CORPO) is None
