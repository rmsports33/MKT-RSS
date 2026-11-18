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


def marca_de(corpo):
    """Texto exato da marca presente no corpo."""
    achado = pv.PADRAO.search(corpo)
    assert achado is not None
    return achado.group(0)


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


def test_corpo_que_nao_e_texto_e_marca_ausente():
    assert pv.validar(None) == {"valido": False, "motivo": "marca_ausente"}
    assert pv.validar(123) == {"valido": False, "motivo": "marca_ausente"}


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
    assert resultado == {"valido": False, "motivo": "manifesto_invalido"}
    assert pv.validar_integridade(adulterado) == {
        "valido": False, "motivo": "manifesto_invalido"
    }


def test_version_sha256_precisa_ser_hexadecimal_completo():
    with pytest.raises(ValueError, match="version_sha256"):
        marcar(version_sha256="v>1")
    with pytest.raises(ValueError, match="version_sha256"):
        marcar(version_sha256="a" * 63)


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


# --- duplicidade e marcador malformado -------------------------------------


def test_validar_rejeita_marcadores_duplicados_identicos():
    corpo, _ = marcar()
    marca = pv.PADRAO.search(corpo).group(0)
    duplicado = corpo + "\n" + marca
    assert pv.validar(duplicado) == {
        "valido": False, "motivo": "marca_duplicada"
    }


def test_validar_rejeita_marcadores_duplicados_conflitantes():
    corpo, _ = marcar()
    manifesto = pv.extrair_manifesto(corpo)
    manifesto["voice_status"] = "NOT_APPLIED"
    conflitante = pv.PREFIXO_MARCA + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + " -->"
    duplicado = corpo + "\n" + conflitante
    assert pv.validar(duplicado) == {
        "valido": False, "motivo": "marca_duplicada"
    }


def test_validar_rejeita_segundo_marcador_malformado():
    corpo, _ = marcar()
    duplicado = corpo + "\n" + pv.PREFIXO_MARCA + "{quebrado"
    assert pv.validar(duplicado) == {
        "valido": False, "motivo": "marca_duplicada"
    }


def test_validar_rejeita_marcador_unico_malformado():
    quebrado = pv.PREFIXO_MARCA + "{quebrado"
    assert pv.validar(quebrado) == {
        "valido": False, "motivo": "manifesto_invalido"
    }


def test_extrair_manifesto_rejeita_marcadores_duplicados():
    corpo, _ = marcar()
    marca = pv.PADRAO.search(corpo).group(0)
    assert pv.extrair_manifesto(corpo + "\n" + marca) is None


# --- reforcos: hash igual, variacoes e simulacao ---------------------------


def test_marca_unica_valida_continua_aceita():
    corpo, manifesto = marcar()
    assert corpo.count("cxeg-package") == 1
    assert pv.validar(corpo) == {"valido": True, "manifesto": manifesto}


def test_duplicacao_identica_reprovada_mesmo_com_hash_igual():
    corpo, manifesto = marcar()
    duplicado = corpo + "\n" + marca_de(corpo)
    # O hash declarado continua batendo com o corpo sem as duas marcas.
    assert pv.hash_corpo(pv.PADRAO.sub("", duplicado)) == manifesto["content_sha256"]
    assert pv.validar(duplicado)["motivo"] == "marca_duplicada"


def test_simulacao_de_segunda_marca_com_caixa_diferente():
    corpo, _ = marcar()
    manifesto = pv.extrair_manifesto(corpo)
    simulado = corpo + "\n<!-- CXEG-PACKAGE:v1:" + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + " -->"
    assert pv.validar(simulado)["motivo"] == "marca_duplicada"


def test_simulacao_de_segunda_marca_sem_espaco_no_comentario():
    corpo, _ = marcar()
    manifesto = pv.extrair_manifesto(corpo)
    simulado = corpo + "\n<!--cxeg-package:v1:" + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + "-->"
    assert pv.validar(simulado)["motivo"] == "marca_duplicada"


def test_simulacao_de_segunda_marca_dentro_do_texto():
    # Texto do artigo citando o prefixo tambem conta: uma marca, sem excecao.
    corpo, _ = marcar()
    alterado = corpo.replace("<h2>Seção</h2>",
                             "<h2>Seção</h2>\n<pre>cxeg-package:v1:{}</pre>")
    assert pv.validar(alterado)["motivo"] == "marca_duplicada"


def test_marca_de_outra_versao_ao_lado_da_valida_nao_passa():
    corpo, _ = marcar()
    assert pv.validar(corpo + "\n<!-- cxeg-package:vX:{} -->")["motivo"] == \
        "marca_duplicada"


def test_marca_malformada_sem_comentario_valido():
    assert pv.validar(CORPO + "\n<!-- cxeg-package:v1: sem chaves -->") == {
        "valido": False, "motivo": "manifesto_invalido"}
    assert pv.validar(CORPO + "\n<!-- cxeg-package:v1 : {} -->") == {
        "valido": False, "motivo": "manifesto_invalido"}


def test_marcar_recusa_corpo_com_marca_residual():
    with pytest.raises(ValueError, match="marca de proveniencia malformada"):
        marcar(CORPO + "\n<!-- cxeg-package:v1:quebrada -->")
    with pytest.raises(ValueError, match="marca de proveniencia malformada"):
        marcar(CORPO + "\n<!-- CXEG-PACKAGE:v1 -->")


def test_integridade_separa_hash_de_requisitos_editoriais():
    corpo, _ = marcar(image_rights_confirmed=False, substance_status="PENDING",
                      voice_status="NOT_APPLIED")
    integrity = pv.validar_integridade(corpo)
    assert integrity["valido"] is True
    assert pv.validar(corpo)["motivo"] == "voz_nao_aplicada"


@pytest.mark.parametrize("mutacao", [
    lambda m: m.update(image_rights_confirmed="false"),
    lambda m: m.update(voice_status="APROVADO"),
    lambda m: m.update(substance_status="APROVADO"),
    lambda m: m.update(version_sha256="x"),
    lambda m: m.update(modules=[]),
    lambda m: m.update(untrusted_flag=True),
])
def test_manifesto_com_tipo_estado_ou_campo_desconhecido_e_rejeitado(mutacao):
    corpo, _ = marcar()
    manifesto = pv.extrair_manifesto(corpo)
    mutacao(manifesto)
    corpo_adulterado = pv.PADRAO.sub("", corpo).rstrip() + "\n" + pv.PREFIXO_MARCA + json.dumps(
        manifesto, ensure_ascii=False, separators=(",", ":")) + " -->"
    resultado = pv.validar_integridade(corpo_adulterado)
    assert resultado == {"valido": False, "motivo": "manifesto_invalido"}


def test_marcar_nao_coage_string_false_para_direitos_confirmados():
    with pytest.raises(ValueError, match="booleano"):
        marcar(image_rights_confirmed="false")
