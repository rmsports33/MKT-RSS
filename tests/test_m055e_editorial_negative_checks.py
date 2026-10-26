"""Contraprovas M05.5-E no GitHub Actions, sem rede ou provedor externo."""
from mkt_flow_p0.editorial_negative_checks import check_preview

SOURCE = "Wi-Fi 7 usa canais de até 320 MHz segundo a fonte."
def check(**fields): return check_preview(SOURCE, fields)

def test_n1_missing_source():
    assert check_preview("", {"texto_markdown":"Wi-Fi 7"})["veredito"] == "BLOQUEADO"
def test_n2_conflicting_sources():
    assert check_preview(SOURCE, {"texto_markdown":"Wi-Fi 7"}, conflicting_sources=True)["veredito"] == "BLOQUEADO"
def test_n3_price_without_date():
    r=check(texto_markdown="Custa R$ 1.999")
    assert "preco_sem_evidencia_datada:texto_markdown" in r["motivos"]
def test_n4_added_ai_number():
    r=check(texto_markdown="Atinge 9000 Mbps.")
    assert "numero_sem_fonte:texto_markdown:9000" in r["motivos"]
def test_n5_fake_lab_test():
    r=check(texto_markdown="Testamos o aparelho em nosso laboratório.")
    assert any("teste_proprio" in x for x in r["motivos"])
def test_n6_no_alerts_never_certifies():
    r=check(texto_markdown="Wi-Fi 7 usa canais de até 320 MHz.")
    assert r["veredito"] == "REVISAO_OBRIGATORIA" and not r["certificacao_factual"]
def test_n7_metadata_checked():
    r=check(titulo_seo="Wi-Fi 8 chega", meta_description="R$ 999",json_ld={"review":"Testamos em nossa bancada."})
    assert any("titulo_seo" in x for x in r["motivos"])
    assert any("meta_description" in x for x in r["motivos"])
    assert any("json_ld" in x for x in r["motivos"])
def test_never_writes():
    assert check(texto_markdown="Wi-Fi 7")["escreveu"] is False
