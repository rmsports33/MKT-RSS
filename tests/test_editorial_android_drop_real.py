"""Ensaio factual: cópia read-only do WordPress #9711 (Android Drop)."""
import json
from pathlib import Path

from mkt_flow_p0.editorial_core_offline import processar


def test_android_drop_9711_processa_html_real_sem_wordpress(tmp_path):
    fixtures = Path(__file__).parent / "fixtures" / "chatgpt_first"
    m = json.loads((fixtures / "android_drop_9711.json").read_text(encoding="utf-8"))
    texto = (fixtures / "android_drop_9711.md").read_text(encoding="utf-8")
    assert m["source_wp_post_id"] == 9711
    assert len(texto.split()) >= 900
    assert len(m["related_articles"]) == 3
    assert len(m["sources"]) >= 4
    assert m["review"]["approved"] is False
    result = processar(fixtures / "android_drop_9711.json", fixtures / "android_drop_9711.md", tmp_path)
    preview = Path(result["html"]).read_text(encoding="utf-8")
    body = Path(result["wordpress_body"]).read_text(encoding="utf-8")
    assert "<h2>" in body
    assert "<table>" in body and "<th>Recurso</th>" in body
    assert "<td>Motion Assist</td>" in body
    assert "| --- |" not in body
    assert "Visão Guiada" in body
    assert "Find Hub" in body
    assert "Fonte" in body
    assert "https://blog.google/" in body
    assert body.count("conexotech.com.br/") >= 3
    assert "noindex" in preview
    assert "noindex" not in body
    assert "<head" not in body
    assert result["wordpress_written"] is False
    assert result["aprovacao_publicacao"] is False
    assert result["factual_review"] == "NAO_VERIFICADO"
    assert result["contrato_editorial"]["veredito"] == "BLOQUEADO"
    assert result["content_sha256"]
    assert "seo_preflight" in result
    assert result["revisao_factual_humana_pendente"] is True
    assert result["fontes_sem_vinculo_canonico"] == list(range(len(m["sources"])))
    assert result["rastreabilidade_claims"] == []
