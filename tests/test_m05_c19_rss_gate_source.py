"""Regressao estatico-conservadora do bloqueio C19 (sem rede/LLM/WP)."""
from pathlib import Path


def test_rss_nao_envia_pass_literal_antes_do_bloqueio_pos_ia():
    source = (Path(__file__).resolve().parents[1] / "pipeline_rss.py").read_text(encoding="utf-8")
    guard = 'if wp_url and os.getenv("WP_USER", "") and os.getenv("WP_APP_PASSWORD", ""):'
    marker = '"motivo": "gate_factual_pos_ia_nao_integrado"'
    publish = "wp_result = publicar_no_wordpress("
    assert source.index(guard) < source.index(marker) < source.index(publish)
    assert '"escreveu": False' in source[source.index(guard):source.index(publish)]
