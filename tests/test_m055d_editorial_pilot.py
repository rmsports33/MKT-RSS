"""Testes do piloto M05.5-D: sem credenciais, sockets, APIs ou WordPress."""
from mkt_flow_p0.editorial_pilot import Policy, evaluate, save_local

SOURCE = "Fonte oficial: Wi-Fi 7 oferece canais de até 320 MHz onde 6 GHz é permitido."
VALID = Policy(True, "modelo-aprovado-de-teste", .5, .001, .002)
def fake(_): return {"titulo_seo": "Wi-Fi 7", "texto_markdown": "Canais de até 320 MHz."}

def test_default_denies():
    assert evaluate(SOURCE, Policy(), fake)["status"] == "BLOQUEADO"
def test_missing_source_never_calls():
    def explode(_): raise AssertionError("chamou executor")
    assert evaluate("", VALID, explode)["motivo"] == "fonte_ausente_ou_excessiva"
def test_invalid_price_limits_never_calls():
    def explode(_): raise AssertionError("chamou executor")
    assert evaluate(SOURCE, Policy(True,"m",0,.001,.002), explode)["motivo"] == "limites_invalidos"
def test_insufficient_budget_never_calls():
    def explode(_): raise AssertionError("chamou executor")
    p = Policy(True,"m",.000001,.001,.002)
    assert evaluate(SOURCE,p,explode)["motivo"] == "orcamento_insuficiente"
def test_no_callback_no_calls():
    assert evaluate(SOURCE,VALID)["motivo"] == "autorizacao_ou_executor_ausente"
def test_previa_never_certifies():
    r = evaluate(SOURCE,VALID,fake)
    assert r["status"] == "PREVIA_PENDENTE_REVISAO"
    assert r["verificacao_factual"] == "NAO_VERIFICADO" and r["escreveu"] is False
    assert r["wordpress"] == "PROIBIDO" and r["fonte_sha256"]
def test_failure_closed():
    def fail(_): raise RuntimeError("simulated")
    assert evaluate(SOURCE,VALID,fail)["motivo"] == "falha_do_executor"
def test_local_report(tmp_path):
    target = tmp_path / "evidence.json"
    save_local(evaluate(SOURCE, Policy()), target)
    assert target.exists()
