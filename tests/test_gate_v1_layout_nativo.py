"""Testes isolados do layout nativo do Gate V1 (sem produção, sem WordPress).

Verifica que o layout é ADITIVO e NÃO contém lógica paralela de aprovação,
filas próprias ou endpoints duplicados.
"""
from pathlib import Path

BASE = Path(__file__).parent.parent / "mkt_flow_p0"


def _read(name):
    return (BASE / name).read_text(encoding="utf-8")


def test_layout_arquivos_existem():
    for name in (
        "gate_v1_layout_nativo.php",
        "gate_v1_layout_nativo_template.php",
        "gate_v1_layout_nativo.css",
        "gate_v1_layout_nativo.js",
    ):
        assert (BASE / name).exists(), name


def test_sem_endpoints_rest_proprios():
    """Não deve registrar rotas REST novas (cxgv1/v1 ou register_rest_route)."""
    for name in ("gate_v1_layout_nativo.php", "gate_v1_layout_nativo_template.php"):
        code = _read(name)
        assert "register_rest_route" not in code, name
        assert "cxgv1/v1" not in code, name


def test_sem_filas_proprias():
    """Não deve criar filas próprias (cxgv1_*_queue)."""
    code = _read("gate_v1_layout_nativo.php")
    assert "cxgv1_publish_queue" not in code
    assert "cxgv1_correction_queue" not in code


def test_usa_mecanismos_nativos():
    code = _read("gate_v1_layout_nativo.php")
    for fn in (
        "cxeg_owner_approve",
        "cxq_process_approved_intent",
        "cxeg_snapshot",
        "cxeg_hash",
        "cxgna_draft_readiness",
        "cxeg_quality_required_checks",
        "cxeg_review_",
    ):
        assert fn in code, fn


def test_duas_colunas_e_preview():
    css = _read("gate_v1_layout_nativo.css")
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "grid-template-columns" in css
    assert "cxgv1nat-list" in tpl
    assert "cxgv1nat-detail" in tpl


def test_tres_abas():
    tpl = _read("gate_v1_layout_nativo_template.php")
    for tab in ("preview", "details", "verification"):
        assert f'data-tab="{tab}"' in tpl, tab


def test_botoes_aprovacao_e_reprovacao():
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "APROVAR E PUBLICAR" in tpl
    assert "NÃO APROVAR" in tpl
    assert "SALVAR RESPOSTA" in tpl


def test_motivos_e_justificativa():
    code = _read("gate_v1_layout_nativo.php")
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "fontes_insuficientes" in code
    assert "alteracao_apos_aprovacao" in code
    assert "cxgv1nat-just" in tpl
    assert "A justificativa é obrigatória" in code


def test_sem_publicacao_automatica_no_aprovador():
    code = _read("gate_v1_layout_nativo.php")
    assert "'hold'" in code
    assert "cxq_process_approved_intent" in code


def test_conectado_a_tela_nativa():
    """Layout conectado via hook admin_notices na página nativa."""
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "add_action('admin_notices', 'cxgv1nat_render_above_native_form'" in tpl
    assert "conexo-owner-review" in tpl


def test_formulario_nativo_por_id_unico():
    """Não usar document.querySelector('form') de forma ambígua."""
    js = _read("gate_v1_layout_nativo.js")
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "document.querySelector('form')" not in js
    assert "cxgv1nat-native-form" in tpl
    assert "getElementById(cfg.formId" in js


def test_nao_marca_13_criterios_automaticamente():
    """JS não marca checks nem cria evidências; PHP exige checks reais."""
    js = _read("gate_v1_layout_nativo.js")
    php = _read("gate_v1_layout_nativo.php")
    assert "c.checked = true" not in js
    assert "Falta verificação humana com evidência" in php
    assert "$checks = array();" not in php


def test_destino_nativo_preservado():
    """JS não altera publication_mode (apenas menção em comentário)."""
    js = _read("gate_v1_layout_nativo.js")
    # Remover comentários para verificar código executável
    code = "\n".join(
        linha for linha in js.splitlines()
        if not linha.strip().startswith("*") and not linha.strip().startswith("//")
    )
    assert "publication_mode" not in code


def test_reprovacao_no_historico_nativo():
    """Reprovação grava em cxeg_review_{id} com decision=rejected."""
    php = _read("gate_v1_layout_nativo.php")
    tpl = _read("gate_v1_layout_nativo_template.php")
    assert "'decision' => 'rejected'" in php
    assert "cxeg_review_" in php
    assert "cxgv1nat_handle_reject" in tpl
    assert "check_admin_referer" in tpl


def test_js_nao_cria_endpoint():
    js = _read("gate_v1_layout_nativo.js")
    assert "register_rest_route" not in js
    assert "/snapshot/" in js  # endpoint nativo existente


def test_nao_modifica_core_nem_mu_plugins():
    """Nenhum arquivo do core ou MU-plugins foi alterado nesta branch."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/master", "--",
         "wp-content/", "mu-plugins/"],
        cwd=Path(__file__).parent.parent,
        capture_output=True, text=True,
    )
    assert result.stdout.strip() == "", result.stdout
