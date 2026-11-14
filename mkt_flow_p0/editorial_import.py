"""Import a researched article into the existing MKT-RSS editorial handoff.

Offline imports never call a provider. Online imports automatically develop and
critique pending prose with the existing provider. Neither path writes WordPress.
"""
import argparse
import json
import hashlib
import os
from pathlib import Path

from mkt_flow_p0.editorial_identity import (
    criar_handoff_chatgpt, salvar_handoff_chatgpt, validar_handoff_chatgpt,
)


def _preparar_handoff(payload):
    """Validate an editor/provider input without side effects."""
    required_payload = {"source_url", "source_name", "article", "research"}
    optional_payload = {"editorial_voice_application", "editorial_brief", "editorial_substance_review", "editorial_contract"}
    if (not isinstance(payload, dict)
            or not required_payload.issubset(payload)
            or set(payload) - required_payload - optional_payload):
        raise ValueError("pacote exige source_url, source_name, article e research; a prova de voz é opcional")
    source_name = payload["source_name"]
    if not isinstance(source_name, str) or not source_name.strip() or len(source_name) > 120:
        raise ValueError("nome da fonte original invalido")
    article = payload["article"]
    required = {"titulo_seo", "meta_description", "slug", "texto_markdown"}
    if not isinstance(article, dict) or set(article) != required:
        raise ValueError("campos do artigo invalidos")
    if (not isinstance(article["texto_markdown"], str)
            or len(article["texto_markdown"].split()) < 200):
        raise ValueError("artigo precisa de ao menos 200 palavras")
    handoff = criar_handoff_chatgpt(
        article, url_fonte=payload["source_url"],
        fonte_nome=source_name, contexto_complementar=payload["research"],
        voice_application=payload.get("editorial_voice_application"),
        editorial_brief=payload.get("editorial_brief"),
        editorial_review=payload.get("editorial_substance_review"),
        editorial_contract=payload.get("editorial_contract"))
    return handoff


def importar_artigo_para_handoff(payload, output_dir):
    """Low-level envelope import, NOT completion of the operational pipeline."""
    handoff = _preparar_handoff(payload)
    path = salvar_handoff_chatgpt(handoff, output_dir)
    return {**validar_handoff_chatgpt(handoff), "handoff_path": path,
            "wordpress_written": False, "provider_called": False}


def processar_artigo_importado(payload, output_dir, *, genero="guia", image_manifest=None, image_base=None, offline=True, image_fit_review=None, development_receipt=None,
                                featured_media_id=None, media_rights_confirmed=False,
                                verified_related_urls=None, force_development=False):
    """Always run editorial triage; online mode develops pending prose automatically.

    Offline mode preserves text and reports pending work. No WordPress writes.
    """
    from mkt_flow_p0.editorial_core_offline import processar, validar_pacote
    from mkt_flow_p0.editorial_readiness import avaliar_prontidao_editorial
    from mkt_flow_p0.gate_editorial_pos_ia import validar_saida
    from mkt_flow_p0.editorial_trace import make_trace, save_trace
    from mkt_flow_p0.adaptador_contrato_editorial import avaliar_snapshot_editorial

    # Reject invalid destinations/inputs before network or provider usage.
    if Path(output_dir).exists():
        raise FileExistsError("diretório de saída já existe")
    if offline and force_development:
        raise ValueError("adaptação online incompatível com offline")
    # Validate/renderability before creating an output directory or handoff.
    handoff = _preparar_handoff(payload)
    errors = validar_pacote(handoff["metadata"], handoff["markdown"])
    if errors:
        raise ValueError("; ".join(errors))
    from mkt_flow_p0.image_protocol import plan_image, validate_prepared_manifest
    if image_manifest is not None:
        if image_base is None:
            raise ValueError("IMAGE_BASE_REQUIRED")
        validate_prepared_manifest(image_manifest, base_dir=image_base)
    from mkt_flow_p0.editorial_substance import assess_substance
    current_assessment = assess_substance(handoff["markdown"],payload.get("editorial_brief"),
                                         payload.get("editorial_substance_review"))
    if payload.get("editorial_brief") is not None and payload["editorial_brief"]["genre"] != genero:
        raise ValueError("gênero do briefing diverge do processamento")
    voice_applied = handoff["metadata"]["editorial_voice_application"]["status"] != "NOT_APPLIED"
    if not offline and development_receipt is None and (force_development or
            current_assessment["status"] != "PASS" or not voice_applied):
        from mkt_flow_p0.editorial_development import adapt_imported_article
        payload, development_receipt = adapt_imported_article(payload, genre=genero)
        handoff = _preparar_handoff(payload)
        errors = validar_pacote(handoff["metadata"], handoff["markdown"])
        if errors:
            raise ValueError("; ".join(errors))
    image_plan = plan_image(payload['article']['titulo_seo'], offline=offline, content_fit=image_fit_review)
    if image_manifest is not None:
        if image_base is None:raise ValueError('IMAGE_BASE_REQUIRED')
        resource = validate_prepared_manifest(image_manifest, base_dir=image_base)
        resource['preview_assets'] = {name:'assets/cover-'+name+'.jpg' for name in ('desktop','mobile')}
        resource['asset_sha256'] = {name:image_manifest['assets'][name]['sha256'] for name in ('desktop','mobile')}
        resource['visual_review'] = image_manifest['visual_review']
        from mkt_flow_p0.editorial_identity import atualizar_handoff_revisao
        handoff = atualizar_handoff_revisao(handoff,handoff['markdown'],image_resource=resource)
        image_plan = {'status':'PREPARED_GENERATED_IMAGE_INSTALLED' if resource.get('source_type') == 'ai_generated' else 'PREPARED_LICENSED_IMAGE_INSTALLED','resource':resource,
                      'network_called':False,'ai_called':resource.get('source_type') == 'ai_generated','wordpress_written':False}
    if featured_media_id is not None:
        from mkt_flow_p0.editorial_identity import atualizar_handoff_revisao
        handoff = atualizar_handoff_revisao(handoff, handoff["markdown"],
            featured_media_id=featured_media_id, media_rights_confirmed=media_rights_confirmed)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    # No overwrite/reused acceptance; each run has an exclusive private directory.
    handoff_path = salvar_handoff_chatgpt(handoff,root)
    imported = {**validar_handoff_chatgpt(handoff),'handoff_path':handoff_path,'wordpress_written':False,'provider_called':False}
    saved = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
    if image_manifest is not None:
        import shutil
        (root/'assets').mkdir(mode=0o700)
        for name in ('desktop','mobile'):
            shutil.copyfile(Path(image_base)/image_manifest['assets'][name]['path'],root/'assets'/('cover-'+name+'.jpg'))
            os.chmod(root/'assets'/('cover-'+name+'.jpg'),0o600)
    metadata_path, markdown_path = root / "article.metadata.json", root / "article.md"
    metadata_path.write_text(json.dumps(saved["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(saved["markdown"], encoding="utf-8")
    rendered = processar(metadata_path, markdown_path, root)
    body = Path(rendered["wordpress_body"]).read_text(encoding="utf-8")
    readiness = avaliar_prontidao_editorial(saved, html=body, genero=genero,
        featured_media_id=featured_media_id, direitos_imagem_confirmados=media_rights_confirmed,
        verified_related_urls=verified_related_urls)
    source_text = "\n".join(fact for source in payload["research"]["sources"] for fact in source["facts"])
    alerts = validar_saida(source_text, saved["markdown"])
    adapter_check = avaliar_snapshot_editorial(saved["metadata"].get("contrato_editorial"))
    trace = make_trace(payload["source_url"], saved["markdown"])
    # An import is not a response generated by Groq, nor human factual approval.
    trace["events"][0] = {"stage": "authoring", "module_id": "mkt-rss.editorial-import",
        "module_version": "import-flow/2", "status": "DEVELOPED_WITH_PROVIDER" if development_receipt else "IMPORTED_NO_PROVIDER",
        "evidence_ref": "content-sha256:" + trace["content_sha256"]}
    trace["events"].append({"stage":"package_validation", "module_id":"mkt-rss.editorial-identity",
        "module_version":"import-flow/1", "status":"PASS"})
    trace_path = save_trace(trace, root)
    result = {"schema":"conexo-imported-editorial-flow/1", **imported,
        "content_sha256":hashlib.sha256(saved["markdown"].encode()).hexdigest(),
        "metadata_path":str(metadata_path),"markdown_path":str(markdown_path),
        "preview_path":rendered["html"],"wordpress_body_path":rendered["wordpress_body"],
        "trace_path":trace_path,"readiness":readiness,"numeric_and_own_test_alerts":alerts,
        "seo_preflight":rendered["seo_preflight"],
        "evidence_contract":rendered["contrato_editorial"],
        "adapter_contract_check":adapter_check,
        "alert_scope":"operator_supplied_research_claims_not_full_source_or_factual_approval",
        "claims_traceability":rendered["rastreabilidade_claims"],
        "modules_executed":["editorial_import","editorial_identity","editorial_core_offline",
            "format","seo","seo_contract_native","editorial_readiness",
            "gate_editorial_pos_ia","adaptador_contrato_editorial","editorial_trace","image_protocol","editorial_substance"],
        "module_manifest":[
            {"id":module_id,"execution":"EXECUTED", "outcome": (
                readiness["status"] if module_id == "editorial_readiness" else
                readiness["avaliacao_substantiva"]["status"] if module_id == "editorial_substance" else
                adapter_check["veredito"] if module_id == "adaptador_contrato_editorial" else
                alerts["veredito"] if module_id == "gate_editorial_pos_ia" else
                image_plan["status"] if module_id == "image_protocol" else "DIAGNOSTIC_ONLY")}
            for module_id in ["editorial_import","editorial_identity","editorial_core_offline",
                "format","seo","seo_contract_native","editorial_readiness",
                "gate_editorial_pos_ia","adaptador_contrato_editorial","editorial_trace","image_protocol","editorial_substance"]
        ],
        "completion_status":readiness["status"],
        "editorial_development": development_receipt or {"execution":"NOT_RUN", "reason":"prewritten_import_preserves_text",
            "next_action":"adapt_imported_article with an authorized provider, or supply a text-bound substantive review"},
        "article_complete_for_human_review":readiness["status"] == "PRONTO_PARA_REVISAO_HUMANA",
        "editorial_voice_application":readiness.get("persona_editorial", {"status":"NOT_APPLIED"}),
        "substantive_review":readiness.get("avaliacao_substantiva"),
        "voice_quality_review":readiness.get("revisao_de_voz", "PENDENTE_AVALIACAO_HUMANA"),
        "image_research":image_plan, "image_generation_request":image_plan.get('generation_request'),
        "image_ai_used":bool(image_plan.get('ai_called')),
        "related_links":"VERIFIED_BY_CALLER" if verified_related_urls else "NOT_VERIFIED",
        "provider_called":bool(development_receipt),"network_called":bool(development_receipt) or image_plan.get("network_called",False),"wordpress_written":False,
        "publication_authorized":False,"human_acceptance":"PENDING"}
    (root / "pipeline-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding="utf-8")
    # All generated artifacts are private even with a permissive process umask.
    for path in root.iterdir():
        if path.is_file():os.chmod(path,0o600)
    return result


def resumo_execucao(result):
    """Safe console receipt; full diagnostics stay in the private directory."""
    keys = ("schema","version_sha256","content_sha256","modules_executed",
        "module_manifest","completion_status","article_complete_for_human_review",
        "editorial_voice_application","voice_quality_review","provider_called",
        "network_called","wordpress_written","publication_authorized","human_acceptance")
    return {k: result[k] for k in keys if k in result}


def main():
    """Offline CLI: import a finished article; never call a model or WordPress."""
    parser = argparse.ArgumentParser(description="Importar artigo para revisao MKT-RSS")
    parser.add_argument("--import-article", type=Path, required=True)
    parser.add_argument("--handoff-dir", type=Path, required=True)
    parser.add_argument("--image-manifest", type=Path)
    parser.add_argument("--image-fit-review", choices=("PASS", "INCONGRUENT"), help="Resultado da revisão visual/editorial da candidata gratuita")
    parser.add_argument("--offline",action="store_true",help="Sem pesquisa de imagem na rede; protocolo ainda avalia catálogo/pendências")
    args = parser.parse_args()
    if args.import_article.stat().st_size > 1024 * 1024:
        parser.error("arquivo excede 1 MiB")
    payload = json.loads(args.import_article.read_text(encoding="utf-8"))
    image = json.loads(args.image_manifest.read_text(encoding='utf-8')) if args.image_manifest else None
    report = processar_artigo_importado(payload, args.handoff_dir,
        image_manifest=image,image_base=args.image_manifest.parent if args.image_manifest else None,offline=args.offline,image_fit_review=args.image_fit_review)
    print(json.dumps(resumo_execucao(report), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
