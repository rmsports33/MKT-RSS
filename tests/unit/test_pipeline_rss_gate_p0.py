"""M04.16D — integração opt-in do gate de valor no pipeline_rss.

Tudo mockado: sem rede, sem LLM e sem WordPress. Os testes provam que:
- sem GATE_PUBLICACAO_ENABLED o comportamento anterior não muda;
- com a flag ligada o gate roda depois da extração e antes da IA;
- bloqueio e erro de validação impedem reescrita e rascunho WP.
"""
from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import pipeline_rss as P

ENV_FLAG = "GATE_PUBLICACAO_ENABLED"
ITEM = {"titulo": "Novo notebook", "resumo": "Review", "link": "https://x/n", "fonte": "blog"}
EXT = {"titulo": "Notebook X", "texto": "corpo " * 500, "palavras": 500,
       "qualidade_ok": True, "imagem": ""}
RW = {"titulo_seo": "Titulo SEO", "meta_description": "m", "slug": "s", "tags": ["t"],
      "texto_markdown": "texto " * 300, "palavras": 300}
COMPLIANCE_OK = {"veredito": "APROVADO", "categorias": [], "trechos": [], "total_sinais": 0}
GATE_OK = {"veredito": "APROVADO", "criterios": ["fonte_primaria"],
           "total_criterios": 1, "motivo": "valor_acrescentado", "aviso": "", "avisos": []}
GATE_BLOQUEADO = {"veredito": "BLOQUEADO", "criterios": [], "total_criterios": 0,
                  "motivo": "sem_valor_acrescentado",
                  "aviso": "Nenhum dos 4 critérios da regra 14.", "avisos": []}


def _nao_deveria_rodar(*args, **kwargs):
    raise AssertionError("gate_publicacao não deveria ser chamado")


def _erro_na_validacao(*args, **kwargs):
    raise RuntimeError("validação indisponível")


@contextmanager
def fluxo_mockado(monkeypatch, tmp_path, gate_resultado=None):
    """Mocka extração, IA, WP e (quando pedido) o gate_publicacao."""
    monkeypatch.setattr(P, "DB_PATH", tmp_path / "rss.db")
    mocks = SimpleNamespace()
    with ExitStack() as stack:
        stack.enter_context(patch(
            "mkt_flow_p0.content_filter.filtrar_item_rss",
            return_value={"veredito": "APROVADO", "categorias": []}))
        stack.enter_context(patch(
            "mkt_flow_p0.extractor.extrair_conteudo", return_value=dict(EXT)))
        stack.enter_context(patch(
            "mkt_flow_p0.content_filter.filtrar_conteudo",
            return_value=dict(COMPLIANCE_OK)))

        if gate_resultado is None:
            mocks.gate = None
        elif callable(gate_resultado):
            mocks.gate = stack.enter_context(patch(
                "mkt_flow_p0.content_filter.gate_publicacao",
                side_effect=gate_resultado))
        else:
            mocks.gate = stack.enter_context(patch(
                "mkt_flow_p0.content_filter.gate_publicacao",
                return_value=gate_resultado))

        mocks.keywords = stack.enter_context(patch(
            "mkt_flow_p0.seo.enriquecer_com_keywords", return_value=["kw"]))
        mocks.rewrite = stack.enter_context(patch(
            "mkt_flow_p0.rewriter.reescrever_materia", return_value=dict(RW)))
        stack.enter_context(patch(
            "mkt_flow_p0.wp_publisher.garantir_categoria", return_value=1))
        stack.enter_context(patch(
            "mkt_flow_p0.wp_publisher.garantir_tag", return_value=2))
        mocks.publish = stack.enter_context(patch(
            "mkt_flow_p0.wp_publisher.publicar_no_wordpress",
            return_value={"post_id": 123, "status": "draft",
                          "link": "https://example.com/?p=123"}))
        stack.enter_context(patch("mkt_flow_p0.links_internos.sugerir", return_value=[]))

        monkeypatch.setenv("WP_URL", "https://example.com")
        monkeypatch.setenv("WP_USER", "tester")
        monkeypatch.setenv("WP_APP_PASSWORD", "test-only")
        yield mocks


# --- Flag de configuração -------------------------------------------------

@pytest.mark.parametrize("valor", ["1", "true", "TRUE", "yes", "on", " on "])
def test_flag_ligada_apenas_com_valor_explicito(monkeypatch, valor):
    monkeypatch.setenv(ENV_FLAG, valor)
    assert P.gate_publicacao_ativo() is True


@pytest.mark.parametrize("valor", ["", "0", "false", "no", "off", "enabled", "sim", "2"])
def test_flag_desligada_para_qualquer_outro_valor(monkeypatch, valor):
    monkeypatch.setenv(ENV_FLAG, valor)
    assert P.gate_publicacao_ativo() is False


def test_flag_ausente_fica_desligada(monkeypatch):
    monkeypatch.delenv(ENV_FLAG, raising=False)
    assert P.gate_publicacao_ativo() is False


# --- Comportamento padrão (gate desligado) ---------------------------------

def test_gate_desligado_nao_invoca_gate_nem_altera_dry_run(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_FLAG, raising=False)
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=_nao_deveria_rodar) as mocks:
        r = P.processar_item(ITEM, dry_run=True)
    assert r["acao"] == "dry_run_ok"
    assert r["palavras"] == 500
    assert mocks.gate.call_count == 0
    assert mocks.rewrite.call_count == 0
    assert mocks.publish.call_count == 0


def test_gate_desligado_mantem_publicacao_de_rascunho(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV_FLAG, raising=False)
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=_nao_deveria_rodar) as mocks:
        r = P.processar_item(ITEM)
    assert r["acao"] == "publicado_rascunho"
    assert r["run_id"]
    assert mocks.gate.call_count == 0
    assert mocks.rewrite.call_count == 1
    assert mocks.publish.call_count == 1


# --- Gate ligado: bloqueio antes da IA e do WP -----------------------------

def test_gate_ligado_bloqueia_antes_da_ia(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FLAG, "1")
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=GATE_BLOQUEADO) as mocks:
        r = P.processar_item(ITEM)
    assert r["acao"] == "bloqueado"
    assert r["motivo"] == "sem_valor_acrescentado"
    assert r["criterios"] == []
    assert r["url"] == "https://x/n"
    assert mocks.keywords.call_count == 0
    assert mocks.rewrite.call_count == 0
    assert mocks.publish.call_count == 0
    assert not (tmp_path / "rss.db").exists()


def test_gate_ligado_bloqueia_tambem_no_dry_run(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FLAG, "true")
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=GATE_BLOQUEADO) as mocks:
        r = P.processar_item(ITEM, dry_run=True)
    assert r["acao"] == "bloqueado"
    assert mocks.rewrite.call_count == 0
    assert mocks.publish.call_count == 0


# --- Gate ligado: aprovação segue o fluxo ---------------------------------

def test_gate_ligado_aprovado_segue_ate_o_rascunho(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FLAG, "yes")
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=GATE_OK) as mocks:
        r = P.processar_item(ITEM)
    assert r["acao"] == "publicado_rascunho"
    assert mocks.gate.call_count == 1
    assert mocks.rewrite.call_count == 1
    assert mocks.publish.call_count == 1


def test_gate_ligado_avalia_conteudo_extraido_antes_da_ia(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FLAG, "on")
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=GATE_OK) as mocks:
        r = P.processar_item(ITEM, dry_run=True)
    assert r["acao"] == "dry_run_ok"
    assert mocks.gate.call_count == 1
    kwargs = mocks.gate.call_args.kwargs
    assert kwargs["titulo"] == EXT["titulo"]
    assert kwargs["texto"] == EXT["texto"]
    assert kwargs["links"] == ["https://x/n"]
    assert mocks.rewrite.call_count == 0
    assert mocks.publish.call_count == 0


# --- Gate ligado: erro bloqueia por segurança ------------------------------

def test_gate_ligado_erro_de_validacao_bloqueia_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FLAG, "1")
    with fluxo_mockado(monkeypatch, tmp_path, gate_resultado=_erro_na_validacao) as mocks:
        r = P.processar_item(ITEM)
    assert r["acao"] == "bloqueado"
    assert r["motivo"] == "erro_validacao_gate"
    assert "validação indisponível" in r["aviso"]
    assert mocks.rewrite.call_count == 0
    assert mocks.publish.call_count == 0
