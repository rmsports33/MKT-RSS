"""M05.2B: impedir reintroducao de publicacao WordPress sem gate factual.

Teste estatico offline: nao depende de rede, WP, LLM ou credenciais.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline_rss.py"


def test_rss_pipeline_nao_invoca_publicador_wordpress():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "publicar_no_wordpress"
    ]
    assert not calls, "RSS nao pode publicar sem certificacao factual"


def test_rss_pipeline_nao_importa_publicador_wordpress():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "mkt_flow_p0.wp_publisher"
    ]
    assert not imports, "RSS nao pode reativar o publicador por import"


def test_rss_pipeline_conserva_bloqueio_factual():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    fn = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "processar_item"
    )
    values = [
        node.value for node in ast.walk(fn)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert "gate_factual_pos_ia_nao_integrado" in values
    assert "NAO_VERIFICADO" in values


def test_rss_bloqueio_factual_e_incondicional_apos_auditorias():
    """O ultimo comando de processar_item deve bloquear, sem desvio WP."""
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "processar_item")
    ultimo = fn.body[-1]
    assert isinstance(ultimo, ast.Return)
    assert isinstance(ultimo.value, ast.Dict)
    itens = {
        chave.value: valor
        for chave, valor in zip(ultimo.value.keys, ultimo.value.values)
        if isinstance(chave, ast.Constant) and isinstance(chave.value, str)
    }
    assert isinstance(itens["acao"], ast.Constant) and itens["acao"].value == "bloqueado"
    assert isinstance(itens["escreveu"], ast.Constant) and itens["escreveu"].value is False
    assert isinstance(itens["verificacao_factual"], ast.Name)
    assert itens["verificacao_factual"].id == "verificacao_factual"
    assert not any(isinstance(node, (ast.If, ast.IfExp)) for node in ast.walk(ultimo))


def test_rss_nao_contorna_gate_por_alias_de_importacao():
    """Evita importacoes indiretas obvias do publicador no pipeline RSS."""
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name == "mkt_flow_p0.wp_publisher" for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "mkt_flow_p0.wp_publisher"
