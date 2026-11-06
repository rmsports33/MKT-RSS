"""Regressões offline da prioridade banco gratuito -> IA no MKT-RSS."""
from unittest.mock import patch

from mkt_flow_p0 import image_handler as ih


def test_banco_gratuito_tem_prioridade_sobre_imagem_rss():
    candidate = {"url": "https://images.unsplash.com/photo-x",
                 "pagina_origem": "https://unsplash.com/photos/abc",
                 "licenca_url": "https://unsplash.com/license",
                 "autor": "Fotógrafa", "origem": "unsplash",
                 "revisao_direitos": "PENDENTE", "revisao_visual": "PENDENTE"}
    with patch.object(ih, "buscar_fallback", return_value={"candidatos": [candidate]}) as stock:
        with patch.object(ih, "baixar_imagem") as download:
            result = ih.preparar_capa("https://publisher.test/img.jpg", "tecnologia")
    stock.assert_called_once()
    download.assert_not_called()
    assert result["origem"] == "banco_gratuito"
    assert result["status"] == "REVISAO_HUMANA_DE_MIDIA"
    assert result["candidatos"][0]["licenca_url"]
    assert result["candidatos"][0]["pagina_origem"]


def test_sem_banco_e_sem_direitos_encaminha_ia_sem_gerar():
    with patch.object(ih, "buscar_fallback", return_value={"erro": "sem resultado", "proxima_etapa": "AVALIAR_GERACAO_IA"}):
        with patch.object(ih, "baixar_imagem") as download:
            result = ih.preparar_capa("https://publisher.test/image.jpg", "celular")
    download.assert_not_called()
    assert result["status"] == "IMAGEM_PENDENTE"
    assert result["proxima_etapa"] == "AVALIAR_GERACAO_IA"
    assert "bytes" not in result


def test_sem_consulta_nao_usa_imagem_rss_nao_autorizada():
    with patch.object(ih, "baixar_imagem") as download:
        result = ih.preparar_capa("https://publisher.test/photo.jpg")
    download.assert_not_called()
    assert result["proxima_etapa"] == "PESQUISA_BANCO_PENDENTE"


def test_api_unsplash_retorna_referencias_sem_aprovar_licenca(monkeypatch):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "token-falso")
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"results": [
                {"width": 800, "height": 500, "urls": {"regular": "https://images.unsplash.com/small"},
                 "links": {"html": "https://unsplash.com/photos/small"}},
                {"width": 1800, "height": 1200,
                 "urls": {"regular": "https://images.unsplash.com/big"},
                 "links": {"html": "https://unsplash.com/photos/big"},
                 "user": {"name": "Artista"}}]}
    with patch.object(ih.requests, "get", return_value=Response()) as req:
        data = ih.buscar_fallback("celular")
    req.assert_called_once()
    assert len(data["candidatos"]) == 1
    photo = data["candidatos"][0]
    assert photo["autor"] == "Artista"
    assert photo["revisao_direitos"] == "PENDENTE"
    assert photo["revisao_visual"] == "PENDENTE"
    assert photo["largura_original"] >= 1200


def test_imagem_original_so_com_confirmacao_e_ainda_pede_conferencia():
    with patch.object(ih, "baixar_imagem", return_value={"bytes": b"fake"}):
        with patch.object(ih, "processar_capa", return_value={"bytes": b"jpeg", "largura": 1200, "altura": 675}):
            result = ih.preparar_capa("https://publisher.test/pic.jpg",
                                     direitos_original_confirmados=True)
    assert result["status"] == "PREVIA_PENDENTE_DE_REVISAO_VISUAL"


def test_ausencia_de_chave_nao_comprova_falta_de_imagens(monkeypatch):
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    with patch.object(ih, "buscar_fallback", return_value={
        "erro": "sem chave", "proxima_etapa": "PESQUISA_BANCO_PENDENTE"}):
        result = ih.preparar_capa(consulta_fallback="noticia tecnologia")
    assert result["proxima_etapa"] == "PESQUISA_BANCO_PENDENTE"
    assert result["status"] == "IMAGEM_PENDENTE"


def test_banco_inacessivel_nao_promove_ia():
    with patch.object(ih, "buscar_fallback", return_value={
        "erro": "falha de rede", "proxima_etapa": "PESQUISA_BANCO_PENDENTE"}):
        result = ih.preparar_capa(consulta_fallback="smartphone")
    assert result["proxima_etapa"] == "PESQUISA_BANCO_PENDENTE"
