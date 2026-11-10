import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from mkt_flow_p0.editorial_substance import (
    CRITERIA, assess_substance, brief_hash, content_hash,
)
from mkt_flow_p0.editorial_development import adapt_imported_article
from mkt_flow_p0.editorial_identity import (
    criar_handoff_chatgpt, atualizar_handoff_revisao, DNA_PROMPT_SHA256,
)
from mkt_flow_p0.editorial_import import processar_artigo_importado
from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial

BRIEF = {"genre":"guia", "reader":"Leitor brasileiro incomodado com trocas de palavras no celular.",
         "need":"Identificar o controle adequado sem desligar funções úteis.",
         "angle":"Separar o sintoma da configuração e mudar uma opção por vez.",
         "contribution":"Comparar escolhas por cenário e explicar o custo de cada decisão.",
         "limits":"Sem teste em aparelho; usar documentação atribuída e exemplos hipotéticos."}
TEXT = """## Comece pelo incômodo, não pelo botão

Se o teclado troca uma palavra que você queria manter, esconder sugestões pode atacar o incômodo errado. Primeiro identifique se houve uma troca ou apenas uma oferta de continuação. Essa distinção orienta a escolha e evita desligar funções que ainda ajudam na escrita.

Imagine um nome próprio que acaba substituído numa mensagem. Esse exemplo é hipotético: serve para distinguir uma correção de uma sugestão, sem apresentar uma experiência de teste da redação. A decisão deve partir do comportamento que você observou no aparelho, e não de uma promessa de que um único ajuste resolve todo problema do teclado.

## Mude uma variável e observe

A recomendação é alterar um controle por vez. Se você muda várias opções juntas, perde a referência de qual delas causava o incômodo. Se a mudança não resolver, retorne à configuração anterior antes de tentar a próxima. Esse procedimento preserva a capacidade de comparar o resultado e dá um caminho de volta ao leitor.

O custo de desligar uma função é abrir mão também da ajuda que ela oferecia. Por isso, para uma ocorrência isolada, vale avaliar uma intervenção pontual antes de uma mudança geral. Já um comportamento recorrente pode justificar rever a preferência correspondente, com atenção ao idioma e à versão documentada.

Este guia organiza decisões a partir da documentação fornecida. Não houve teste próprio em aparelho; disponibilidade, nomes dos controles e dependências precisam ser conferidos nas fontes e na versão instalada antes de publicar as instruções específicas.
"""


def review(text=TEXT, score=3):
    paragraphs = [p for p in text.split("\n\n") if len(p) > 80]
    return {"method":"assisted", "reviewer":"test-fixture-not-human-approval",
            "content_sha256":content_hash(text), "brief_sha256":brief_hash(BRIEF),
            "criteria":{key:{"score":score, "reason":"Fixture de roteamento; não comprova julgamento semântico independente.",
                             "excerpt":paragraphs[i % len(paragraphs)]}
                        for i,key in enumerate(CRITERIA)}}


def payload():
    return {"source_url":"https://example.org/source", "source_name":"Fonte de teste",
            "article":{"titulo_seo":"Como escolher o ajuste do teclado", "slug":"ajuste-teclado",
                       "meta_description":"Entenda qual comportamento do teclado incomoda antes de mudar controles e preserve funções úteis, com atenção aos limites da documentação.",
                       "texto_markdown":TEXT},
            "research":{"sources":[{"name":"Documento complementar", "url":"https://example.org/other",
                                     "facts":["As instruções dependem da versão do sistema e do idioma selecionado."]}]},
            "editorial_brief":copy.deepcopy(BRIEF), "editorial_substance_review":review(),
            "editorial_voice_application":{"status":"HUMAN_ADAPTED", "method":"human_editorial_check",
                "dna_prompt_sha256":DNA_PROMPT_SHA256, "content_sha256":content_hash(TEXT),
                "editor":"Test fixture; not real human approval"}}


def test_prompt_proof_cannot_replace_substantive_assessment():
    assert assess_substance(TEXT, BRIEF)["status"] == "PENDING"
    assert assess_substance(TEXT, BRIEF, review())["status"] == "PASS"
    assert not assess_substance(TEXT, BRIEF, review())["publication_authorized"]


@pytest.mark.parametrize("mutate", [
    lambda r:r.update(content_sha256="a"*64),
    lambda r:r.update(brief_sha256="a"*64),
    lambda r:r["criteria"].pop("voice"),
    lambda r:r["criteria"]["voice"].update(excerpt="A fabricated excerpt that never appeared in the actual article."),
    lambda r:r["criteria"]["voice"].update(score=True),
    lambda r:r["criteria"]["voice"].update(reason="generic"),
])
def test_stale_or_fabricated_assessment_cannot_pass(mutate):
    value=review();mutate(value)
    assert assess_substance(TEXT, BRIEF, value)["status"] == "PENDING"


def test_new_brief_or_edit_invalidates_review():
    changed=dict(BRIEF, angle="Um recorte editorial diferente exige nova avaliação do texto.")
    assert assess_substance(TEXT, changed, review())["status"] == "PENDING"
    assert assess_substance(TEXT+" Uma alteração.", BRIEF, review())["status"] == "PENDING"


def test_repeated_prose_fails_even_with_high_supplied_scores():
    text=(TEXT.split("\n\n")[1]+"\n\n")*10
    assert "repeticao_substantiva" in assess_substance(text, BRIEF, review(text,4))["pendencias"]


def test_content_edit_removes_assessment_and_old_human_attestation():
    p=payload()
    handoff=criar_handoff_chatgpt(p["article"], url_fonte=p["source_url"],
        voice_application=p["editorial_voice_application"], editorial_brief=BRIEF, editorial_review=review())
    updated=atualizar_handoff_revisao(handoff, TEXT+"\n\nNova edição para revisão.")
    assert "editorial_substance_review" not in updated["metadata"]
    assert updated["metadata"]["editorial_voice_application"]["status"] == "NOT_APPLIED"


def test_complete_package_requires_substance_but_never_authorizes_publication():
    p=payload()
    h=criar_handoff_chatgpt(p["article"],url_fonte=p["source_url"], contexto_complementar=p["research"],
        voice_application=p["editorial_voice_application"], editorial_brief=BRIEF, editorial_review=review())
    urls=["https://conexotech.com.br/"+c+"/" for c in "abc"]
    html='<h2>A</h2><h2>B</h2>'+''.join('<a href="'+u+'">Link</a>' for u in urls)
    r=avaliar_prontidao_editorial(h,html=html,genero="guia",featured_media_id=1,
                                direitos_imagem_confirmados=True,verified_related_urls=urls)
    assert r["status"] == "PRONTO_PARA_REVISAO_HUMANA"
    assert r["pronto_para_publicar"] is False
    assert r["revisao_factual"] == "PENDENTE"


def test_import_always_runs_substance_without_provider(tmp_path):
    p=payload();p.pop("editorial_substance_review")
    result=processar_artigo_importado(p,tmp_path/"out")
    assert not result["article_complete_for_human_review"]
    assert result["editorial_development"]["execution"] == "NOT_RUN"
    assert result["substantive_review"]["status"] == "PENDING"
    assert not result["provider_called"]


def test_development_revises_once_after_bad_critique_and_preserves_sources():
    seen=[]
    def writer(title,text,**kwargs):
        seen.append(kwargs)
        return payload()["article"]
    counter=[]
    def critic(text,brief):
        counter.append(1)
        return review(text,2 if len(counter)==1 else 3)
    p=payload();original=copy.deepcopy(p)
    revised,receipt=adapt_imported_article(p,writer=writer,reviewer=critic)
    assert len(seen)==2 and seen[1]["editorial_feedback"] is not None
    assert seen[0]["editorial_brief"]==seen[1]["editorial_brief"]==BRIEF
    assert receipt["outcome"]=="PASS" and receipt["human_acceptance"]=="PENDING"
    assert revised["research"]==p["research"] and p==original
    assert "editorial_voice_application" not in revised  # no invented provider receipt


def test_failed_critic_stops_at_budget_and_remains_pending():
    def failing(*args):raise RuntimeError("private provider error")
    result,receipt=adapt_imported_article(payload(),writer=lambda *a,**kw:payload()["article"],reviewer=failing)
    assert len(receipt["attempts"])==2
    assert receipt["outcome"]=="PENDING"
    assert result["editorial_substance_review"] is None


def test_invalid_brief_never_calls_provider():
    p=payload();p["editorial_brief"]={"angle":"invalid"}
    with pytest.raises(ValueError):
        adapt_imported_article(p,writer=lambda *a,**k:pytest.fail("provider called"))


def test_offline_cli_rejects_provider_flag_before_writing(tmp_path):
    path=tmp_path/"input.json";path.write_text(json.dumps(payload()))
    run=subprocess.run([sys.executable,"pipeline_rss.py","--import-article",str(path),
                        "--handoff-only","--handoff-dir",str(tmp_path/"out"),
                        "--offline","--adapt-editorial"],capture_output=True,text=True,
                       cwd=Path(__file__).resolve().parents[1])
    assert run.returncode!=0 and not (tmp_path/"out").exists()


def test_long_source_is_not_silently_cut_and_oversized_source_is_rejected():
    from mkt_flow_p0.rewriter import montar_prompt
    source="Informação documentada. "*450+"MARCADOR_FIM_DA_APURACAO"
    assert len(source)>9000
    assert "MARCADOR_FIM_DA_APURACAO" in montar_prompt("Título",source,editorial_brief=BRIEF)
    with pytest.raises(ValueError):
        montar_prompt("Título","x"*60001,editorial_brief=BRIEF)


def test_import_forwards_media_and_verified_link_evidence(tmp_path):
    p=payload()
    urls=["https://conexotech.com.br/"+c+"/" for c in "abc"]
    p["article"]["texto_markdown"] += "\n\n"+" ".join("[Relacionado]("+u+")" for u in urls)
    p.pop("editorial_voice_application");p.pop("editorial_substance_review")
    result=processar_artigo_importado(p,tmp_path/"out", featured_media_id=12,
                                    media_rights_confirmed=True, verified_related_urls=urls)
    assert result["readiness"]["imagem_destacada_confirmada"]
    assert result["readiness"]["links_internos_verificados"]==3
    assert not result["article_complete_for_human_review"]  # missing editorial evidence stays visible


def test_truncated_provider_response_is_not_an_article(monkeypatch):
    from types import SimpleNamespace
    from mkt_flow_p0 import rewriter
    response=SimpleNamespace(choices=[SimpleNamespace(finish_reason="length",message=SimpleNamespace(
        content=json.dumps(payload()["article"])) )])
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **k:response)))
    monkeypatch.setattr(rewriter,"_get_client",lambda:(client,""))
    result=rewriter.reescrever_materia("Título",TEXT,editorial_brief=BRIEF)
    assert "truncada" in result["erro"]


def test_online_import_develops_pending_text_without_opt_in(tmp_path,monkeypatch):
    from mkt_flow_p0 import editorial_development, image_protocol
    p=payload();p.pop("editorial_substance_review")
    called=[]
    def adapt(value,**kwargs):
        called.append(kwargs)
        result=copy.deepcopy(value);result["editorial_substance_review"]=review()
        return result,{"execution":"EXECUTED","outcome":"PASS","provider_called":True}
    monkeypatch.setattr(editorial_development,"adapt_imported_article",adapt)
    monkeypatch.setattr(image_protocol,"plan_image",lambda *a,**k:{"status":"PENDING","network_called":False})
    result=processar_artigo_importado(p,tmp_path/"out",offline=False)
    assert called==[{"genre":"guia"}]
    assert result["provider_called"] and result["network_called"]
    trace=json.loads(Path(result["trace_path"]).read_text())
    assert trace["events"][0]["status"]=="DEVELOPED_WITH_PROVIDER"


def test_invalid_output_path_never_calls_provider(tmp_path,monkeypatch):
    from mkt_flow_p0 import editorial_development
    monkeypatch.setattr(editorial_development,"adapt_imported_article",lambda *a,**k:pytest.fail("provider called"))
    with pytest.raises(FileExistsError):
        processar_artigo_importado(payload(),tmp_path,offline=False)


def test_assisted_adaptation_never_impersonates_human_or_system_prompt():
    p=payload()
    proof={"status":"ASSISTED_ADAPTED","method":"assisted_editorial_adaptation",
           "dna_prompt_sha256":DNA_PROMPT_SHA256,"provider_id":"codex",
           "content_sha256":content_hash(TEXT)}
    handoff=criar_handoff_chatgpt(p["article"],url_fonte=p["source_url"],voice_application=proof)
    from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
    assert validar_handoff_chatgpt(handoff)["valid"]
    updated=atualizar_handoff_revisao(handoff,TEXT+" Uma alteração substancial.")
    assert updated["metadata"]["editorial_voice_application"]["status"]=="NOT_APPLIED"


def test_rss_automatically_plans_critiques_revises_and_binds_final_text(monkeypatch):
    from types import SimpleNamespace
    import pipeline_rss
    from mkt_flow_p0 import rewriter,extractor,content_filter,seo,image_protocol
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        if len(calls)==1:
            value=BRIEF
        elif len(calls) in (2,4):
            value=payload()["article"]
        else:
            data=json.loads(kwargs["messages"][1]["content"])
            value={"criteria":review(data["article"],2 if len(calls)==3 else 3)["criteria"]}
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",message=SimpleNamespace(
            content=json.dumps(value)))],usage=None)
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(rewriter,"_get_client",lambda:(client,""))
    monkeypatch.setattr(extractor,"extrair_conteudo",lambda *a:{"titulo":"Teclado do iPhone", "texto":TEXT,
        "qualidade_ok":True,"palavras":len(TEXT.split())})
    for name in ("filtrar_por_tema","filtrar_item_rss","filtrar_conteudo"):
        monkeypatch.setattr(content_filter,name,lambda *a,**kw:{"veredito":"APROVADO"})
    monkeypatch.setattr(seo,"enriquecer_com_keywords",lambda *a,**kw:[])
    monkeypatch.setattr(image_protocol,"plan_image",lambda *a,**kw:{"status":"PENDING"})
    monkeypatch.delenv("CONEXO_RSS_RELATED_LINKS",raising=False)
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED",raising=False)
    result=pipeline_rss.processar_item({"titulo":"Teclado do iPhone","fonte":"Apple",
        "resumo":"Configuração do teclado", "link":payload()["source_url"],"genero":"guia"},
        handoff_only=True,contexto_complementar=payload()["research"])
    assert len(calls)==5  # planning + two writes + two critiques; no hidden retries
    assert result["acao"]=="pacote_editorial_criado" and not result["escreveu"]
    handoff=result["editorial_handoff"]
    assert handoff["metadata"]["editorial_substance_review"]["content_sha256"]==content_hash(handoff["markdown"])
    assert "Crítica da versão anterior" in calls[3]["messages"][1]["content"]
    assert handoff["metadata"]["review"]=={"approved":False}
    assert result["qualidade_editorial"]["desenvolvimento"]["attempts"][-1]["review_diagnostic"]=="REVIEW_ATTACHED"


def test_runtime_does_not_keep_using_obsolete_editorial_build():
    workflow=(Path(__file__).resolve().parents[1]/".github/workflows/rss-homolog-manual.yml").read_text()
    assert 'ref: ${{ github.sha }}' in workflow
    assert '897c38e1fffde6b94608e1f90bd04601b39d6ec8' not in workflow


def test_no_artificial_internal_link_quota_or_unverified_links():
    p=payload()
    h=criar_handoff_chatgpt(p["article"],url_fonte=p["source_url"],contexto_complementar=p["research"],
        voice_application=p["editorial_voice_application"],editorial_brief=BRIEF,editorial_review=review())
    kwargs={"genero":"guia","featured_media_id":1,"direitos_imagem_confirmados":True}
    zero=avaliar_prontidao_editorial(h,html='<h2>A</h2><h2>B</h2>',**kwargs)
    assert zero["status"]=="PRONTO_PARA_REVISAO_HUMANA"
    one=avaliar_prontidao_editorial(h,html='<h2>A</h2><h2>B</h2><a href="https://conexotech.com.br/relevante/">Contexto</a>',
        verified_related_urls=['https://conexotech.com.br/relevante/'],**kwargs)
    assert one["status"]=="PRONTO_PARA_REVISAO_HUMANA"
    fake=avaliar_prontidao_editorial(h,html='<h2>A</h2><h2>B</h2><a href="https://conexotech.com.br/inventado/">Link</a>',**kwargs)
    assert "links_internos_nao_verificados" in fake["pendencias"]


@pytest.mark.parametrize("failure_stage,expected", [
    ("provider", "PROVIDER_REVIEW_FAILED"),
    ("attachment", "REVIEW_ATTACHMENT_FAILED"),
])
def test_rss_review_failure_diagnostic_is_redacted_and_never_passes(monkeypatch, failure_stage, expected):
    from types import SimpleNamespace
    import pipeline_rss
    from mkt_flow_p0 import (
        rewriter, extractor, content_filter, seo, image_protocol,
        editorial_development, editorial_identity,
    )

    def create(**kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content=json.dumps(payload()["article"])),
            )],
            usage=None,
        )
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(rewriter, "_get_client", lambda: (client, ""))
    monkeypatch.setattr(extractor, "extrair_conteudo", lambda *args: {
        "titulo": "Teclado do iPhone", "texto": TEXT,
        "qualidade_ok": True, "palavras": len(TEXT.split()),
    })
    for name in ("filtrar_por_tema", "filtrar_item_rss", "filtrar_conteudo"):
        monkeypatch.setattr(content_filter, name, lambda *a, **kw: {"veredito": "APROVADO"})
    monkeypatch.setattr(seo, "enriquecer_com_keywords", lambda *a, **kw: [])
    monkeypatch.setattr(image_protocol, "plan_image", lambda *a, **kw: {"status": "PENDING"})
    monkeypatch.delenv("CONEXO_RSS_RELATED_LINKS", raising=False)
    monkeypatch.delenv("GATE_PUBLICACAO_ENABLED", raising=False)

    def fail(*a, **kw):
        raise ValueError("private provider or editorial response detail must not leak")
    if failure_stage == "provider":
        monkeypatch.setattr(editorial_development, "review_with_provider", fail)
    else:
        monkeypatch.setattr(editorial_development, "review_with_provider",
                            lambda article, brief: review(article))
        monkeypatch.setattr(editorial_identity, "vincular_avaliacao_substantiva", fail)

    item={"titulo":"Teclado do iPhone", "fonte":"Apple",
          "resumo":"Configuração do teclado", "link":payload()["source_url"],
          "genero":"guia", "editorial_brief":BRIEF}
    result=pipeline_rss.processar_item(
        item, handoff_only=True, contexto_complementar=payload()["research"])
    assert result["acao"] == "pacote_editorial_criado"
    assert result["escreveu"] is False
    assert result["qualidade_editorial"]["desenvolvimento"]["outcome"] == "PENDING"
    attempts=result["qualidade_editorial"]["desenvolvimento"]["attempts"]
    assert len(attempts)==1
    assert attempts[0]["review_diagnostic"]==expected
    assert not attempts[0]["assessment"]["review_valid"]
    assert "editorial_substance_review" not in result["editorial_handoff"]["metadata"]
    assert "private provider or editorial response detail" not in json.dumps(result)

    receipt = pipeline_rss.resumo_seguro_cli("apple-fixture", result)
    assert receipt["review_diagnostics"] == [expected]
    assert receipt["review_attempt_count"] == 1
    assert "private provider or editorial response detail" not in json.dumps(receipt)

    monkeypatch.setattr(
        editorial_identity, "atualizar_handoff_revisao",
        lambda *a, **kw: (_ for _ in ()).throw(ValueError("private article content")),
    )
    blocked = pipeline_rss.processar_item(
        item, handoff_only=True, contexto_complementar=payload()["research"])
    assert blocked["acao"] == "falha"
    assert blocked["motivo"] == "handoff_version_update_failed"
    assert blocked["escreveu"] is False
    safe_blocked = pipeline_rss.resumo_seguro_cli("apple-fixture", blocked)
    assert safe_blocked["motivo"] == "handoff_version_update_failed"
    assert "private article content" not in json.dumps(safe_blocked)
