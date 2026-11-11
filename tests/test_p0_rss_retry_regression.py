"""Regressões P0 do RSS: testes isolados, sem rede ou WordPress.

O cenário xfail documenta a falha conhecida e deve ser removido quando
o pipeline passar a confirmar processamento antes de marcar como visto.
"""
from unittest.mock import Mock

import pytest

from mkt_flow_p0 import rss_ingestor


@pytest.fixture
def noticia(monkeypatch):
    item = {
        "titulo": "Notícia fictícia para teste",
        "link": "https://example.invalid/noticia-p0",
        "published": "",
        "resumo": "Conteúdo de teste",
    }
    monkeypatch.setattr(
        rss_ingestor,
        "fetch_feed",
        lambda *args, **kwargs: {"fonte": "fixture", "itens": [item], "total": 1},
    )
    monkeypatch.setattr(rss_ingestor, "item_ja_visto", lambda *args: False)
    marcador = Mock()
    monkeypatch.setattr(rss_ingestor, "marcar_visto", marcador)
    return item, marcador


def test_dry_run_nao_marca_item_como_visto(noticia):
    """O caminho sem marcação deve continuar seguro para testes."""
    item, marcador = noticia
    resultado = rss_ingestor.buscar_novidades(
        "https://example.invalid/feed", fonte="fixture", limit=1, marcar=False
    )
    assert resultado["novos"] == [item]
    marcador.assert_not_called()


@pytest.mark.xfail(
    strict=True,
    reason="P0 conhecido: buscar_novidades(marcar=True) marca antes de confirmar processamento",
)
def test_p0_descoberta_nao_deve_confirmar_item_antes_do_processamento(noticia):
    """Contrato futuro: descobrir itens não é concluir seu processamento."""
    item, marcador = noticia
    resultado = rss_ingestor.buscar_novidades(
        "https://example.invalid/feed", fonte="fixture", limit=1, marcar=True
    )
    assert resultado["novos"] == [item]
    marcador.assert_not_called()
