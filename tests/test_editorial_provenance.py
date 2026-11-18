"""Proveniencia do corpo: marca gerada pelo motor e detectavel pelo Gate."""
from mkt_flow_p0.editorial_provenance import MODULOS_OBRIGATORIOS, marcar, validar

MODULOS = {m: "EXECUTED" for m in MODULOS_OBRIGATORIOS}


def _marcar(**overrides):
    kwargs = dict(modules=MODULOS, voice_status="PROMPT_APPLIED",
                  substance_status="PASS", image_rights_confirmed=True,
                  version_sha256="abc123")
    kwargs.update(overrides)
    return marcar("<p>Texto do artigo gerado pelo motor.</p>", **kwargs)


def test_corpo_marcado_e_valido():
    corpo, manifesto = _marcar()
    resultado = validar(corpo)
    assert resultado["valido"] is True
    assert manifesto["content_sha256"] == resultado["manifesto"]["content_sha256"]


def test_texto_alterado_invalida():
    corpo, _ = _marcar()
    assert validar(corpo.replace("Texto", "Texto alterado"))["motivo"] == "hash_divergente"


def test_sem_marca_bloqueia():
    assert validar("<p>texto avulso</p>")["motivo"] == "marca_ausente"


def test_sem_prova_de_voz_bloqueia():
    corpo, _ = _marcar(voice_status="NOT_APPLIED")
    assert validar(corpo)["motivo"] == "voz_nao_aplicada"


def test_sem_avaliacao_substantiva_bloqueia():
    corpo, _ = _marcar(substance_status="PENDING")
    assert validar(corpo)["motivo"] == "avaliacao_substantiva_pendente"


def test_sem_direito_de_imagem_bloqueia():
    corpo, _ = _marcar(image_rights_confirmed=False)
    assert validar(corpo)["motivo"] == "direitos_de_imagem_pendentes"


def test_modulo_ausente_bloqueia():
    incompletos = dict(MODULOS)
    incompletos.pop("editorial_substance")
    corpo, _ = _marcar(modules=incompletos)
    assert validar(corpo)["motivo"] == "modulos_ausentes"
