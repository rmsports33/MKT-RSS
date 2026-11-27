"""WordPress-first adapter integration tests; fake API, no real site/secret."""
import json
import tempfile
from pathlib import Path
import unittest

from mkt_flow_p0.wp_quality_executor import WPReadError, WPClient, _NoRedirect, review_once, _private_db
from mkt_flow_p0.revisor_qualidade_unico import _sha, _txt
from mkt_flow_p0.wp_quality_executor import _gate_snapshot_sha


def post_fixture():
    return {
        "id": 9768, "status": "draft", "type": "post",
        "author": 3, "date_gmt": "2026-11-11T10:00:00",
        "title": {"raw": "Android MCP: como agentes de IA vao conectar aplicativos"},
        "content": {"raw": (
            "<p>Google apresentou recurso experimental no Android.</p>" * 80 +
            '<p><a href="https://developer.android.com/ai/appfunctions">AppFunctions</a></p>' +
            '<a href="https://conexotech.com.br/android-drop-recursos-como-conferir/">1</a>' +
            '<a href="https://conexotech.com.br/microsoft-ia-altera-falas-labios-video-ao-vivo/">2</a>' +
            '<a href="https://conexotech.com.br/ceo-da-anthropic-pede-freio-na-ia-e-alerta-risco-online/">3</a>')},
        "excerpt": {"raw": "Texto de resumo editorial suficientemente longo sobre agentes de IA do Android e seus limites para usuários brasileiros."},
        "slug": "android-mcp-agentes-ia-conectar-aplicativos",
        "categories": [10], "featured_media": 9714,
    }


class FakeWP:
    def __init__(self, mutate=False):
        self.p = post_fixture()
        self.calls = 0
        self.mutate = mutate
        self.writes = []
    def post(self, post_id):
        self.calls += 1
        if self.mutate and self.calls == 2:
            self.p["title"]["raw"] += " mudanca"
        return json.loads(json.dumps(self.p))
    def media(self, _id):
        return {"id": 9714, "alt_text": "Android",
                "description": "Pexels license: https://www.pexels.com/license/"}
    def gate_snapshot(self, post_id):
        snapshot, sha = _gate_snapshot_sha(self.p)
        return {"snapshot": snapshot, "snapshot_sha256": sha}
    def submit_quality(self, post_id, report, snapshot_sha):
        self.writes.append((post_id, snapshot_sha))
        return {"recorded": True, "post_id": post_id, "snapshot_sha256": snapshot_sha}
    def published_pages(self, limit=75):
        return [{"page_id":"101","title":"Redes elétricas e data centers",
                 "url":"https://conexotech.com.br/redes-eletricas-data-centers/",
                 "status":"publish"}][:limit]


def complete_evidence(post):
    return {
        "fontes": [{"url": "https://developer.android.com/ai/appfunctions",
                    "verificada": True, "alegacoes": ["Experimental"]}],
        "corpo_original_fonte": _txt(post["content"]),
        "evidencias": {key: {"fingerprint": _sha(post), "reviewer": "synthetic-test-reviewer",
                             "aprovado": True, "referencias": ["synthetic-test-only"]}
                       for key in ("licenca_imagem", "alegacoes", "links_internos",
                                   "revisao_substantiva", "visual_390", "visual_1440")},
    }


class TestCloudAdapter(unittest.TestCase):
    def test_complete_report_bound_to_gate_snapshot_and_ack(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            report, response = review_once(client, 9768, complete_evidence(client.p),
                                          str(Path(root) / "private.db"), submit_quality=True)
            self.assertEqual(report["veredito"], "APTO_PARA_APROVACAO")
            self.assertTrue(response["recorded"])
            self.assertEqual(len(client.writes), 1)
            self.assertFalse(report["publicacao_autorizada"])

    def test_mismatched_gate_snapshot_never_submits(self):
        for field, value in (("post_content", "different manuscript"),
                             ("post_author", 99), ("ID", 99),
                             ("post_status", "publish")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as root:
                client = FakeWP()
                original = client.gate_snapshot
                def altered(post_id):
                    snapshot = original(post_id)
                    snapshot["snapshot"][field] = value
                    return snapshot
                client.gate_snapshot = altered
                with self.assertRaisesRegex(WPReadError, "does not match"):
                    review_once(client, 9768, complete_evidence(client.p),
                                str(Path(root) / "private.db"), submit_quality=True)
                self.assertEqual(client.writes, [])

    def test_malformed_or_wrong_snapshot_hash_never_submits(self):
        for sha in ("z" * 64, "a" * 64, "a" * 63, None):
            with self.subTest(sha=sha), tempfile.TemporaryDirectory() as root:
                client = FakeWP()
                original = client.gate_snapshot
                def altered(post_id):
                    result = original(post_id)
                    result["snapshot_sha256"] = sha
                    return result
                client.gate_snapshot = altered
                with self.assertRaises(WPReadError):
                    review_once(client, 9768, complete_evidence(client.p),
                                str(Path(root) / "private.db"), submit_quality=True)
                self.assertEqual(client.writes, [])

    def test_promotion_or_author_change_on_last_read_never_submits(self):
        for field, value in (("status", "publish"), ("status", "future"),
                             ("author", 99), ("date_gmt", "2026-11-12T10:00:00")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as root:
                client = FakeWP()
                original = client.post
                def altered(post_id):
                    post = original(post_id)
                    if client.calls == 3:
                        post[field] = value
                    return post
                client.post = altered
                with self.assertRaises(WPReadError):
                    review_once(client, 9768, complete_evidence(client.p),
                                str(Path(root) / "private.db"), submit_quality=True)
                self.assertEqual(client.writes, [])

    def test_ack_must_bind_post_and_snapshot(self):
        for ack in ({"recorded": True}, {"recorded": True, "post_id": 99},
                    {"recorded": True, "post_id": 9768, "snapshot_sha256": "a" * 64}):
            with self.subTest(ack=ack), tempfile.TemporaryDirectory() as root:
                client = FakeWP()
                client.submit_quality = lambda *args: ack
                with self.assertRaisesRegex(WPReadError, "acknowledge"):
                    review_once(client, 9768, complete_evidence(client.p),
                                str(Path(root) / "private.db"), submit_quality=True)

    def test_gate_binding_requires_raw_fields_and_normalizes_date_and_categories(self):
        post = post_fixture()
        post["categories"] = [30, 10]
        snapshot, sha = _gate_snapshot_sha(post)
        self.assertEqual(snapshot["post_date_gmt"], "2026-11-11 10:00:00")
        self.assertEqual(snapshot["post_category"], [10, 30])
        self.assertEqual(len(sha), 64)
        post["content"] = {"rendered": "Rendered fallback forbidden"}
        with self.assertRaises(WPReadError):
            _gate_snapshot_sha(post)

    def test_rascunho_realista_readonly_e_sqlite_privado(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            report, remote = review_once(client, 9768, {}, str(Path(root) / "private.db"))
            self.assertEqual(report["post_id"], 9768)
            self.assertEqual(report["veredito"], "REVISAO_NECESSARIA")
            self.assertIsNone(remote)
            self.assertEqual(client.writes, [])
            self.assertTrue((Path(root) / "private.db").exists())
            import sqlite3
            with sqlite3.connect(str(Path(root) / "private.db")) as db:
                self.assertEqual(db.execute("select count(*) from quality_reviews").fetchone()[0], 1)

    def test_sqlite_symlink_is_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "real.sqlite"
            target.write_bytes(b"preserve-this")
            link = Path(root) / "private.sqlite"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "Symlink DB forbidden"):
                _private_db(str(link))
            self.assertEqual(target.read_bytes(), b"preserve-this")

    def test_concurrent_edit_fails_before_save(self):
        with tempfile.TemporaryDirectory() as root:
            db = str(Path(root) / "private.db")
            with self.assertRaises(WPReadError):
                review_once(FakeWP(mutate=True), 9768, {}, db)
            self.assertFalse(Path(db).exists())

    def test_wrong_domain_and_url_components_fail_closed(self):
        for url in ("https://evil.invalid", "http://conexotech.com.br",
                    "https://conexotech.com.br:444", "https://conexotech.com.br/other",
                    "https://conexotech.com.br?redirect=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                WPClient(url, "editor", "test-app-password")

    def test_redirect_rejected_before_authorization_leaves_origin(self):
        handler = _NoRedirect()
        from urllib.request import Request
        with self.assertRaises(WPReadError):
            handler.redirect_request(Request("https://conexotech.com.br/wp-json/wp/v2/posts/1"),
                                     None, 302, "redirect", {}, "https://evil.invalid/steal")

    def test_published_post_never_generates_review_or_submission(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            client.p["status"] = "publish"
            db = str(Path(root) / "report.db")
            with self.assertRaises(WPReadError):
                review_once(client, 9768, {}, db, submit_quality=True)
            self.assertFalse(Path(db).exists())
            self.assertEqual(client.writes, [])

    def test_no_remote_submission_of_partial_review(self):
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            with self.assertRaises(WPReadError):
                review_once(client, 9768, {}, str(Path(root) / "private.db"), submit_quality=True)
            self.assertEqual(client.writes, [])

    def test_opt_in_asve_uses_independent_analyzer_and_stores_bound_receipt(self):
        from mkt_flow_p0.editorial_secondary_analysis import SCHEMA
        with tempfile.TemporaryDirectory() as root:
            client = FakeWP()
            dossier = {
                "sources": [{
                    "source_id":"s1", "url":"https://www.epe.gov.br/pde", "publisher":"EPE",
                    "source_type":"planning_document","source_role":"primary_origin",
                    "published_at":"2026-11-01","reference_period":"2026-2036",
                    "locator":"Caderno de demanda, tabela 1",
                    "methodology":"Cenário EPE publicado",
                    "limitations":"Projeção condicionada a premissas",
                    "retrieved_at":"2026-11-27T10:00:00Z"
                }],
                "claims": [{
                    "claim_id":"c1","claim_text":"A EPE projeta crescimento.",
                    "source_ids":["s1"],"source_role":"primary_origin",
                    "verification_status":"PROJETADA"
                }]
            }
            seen = []
            def analyzer(prompt):
                seen.append(prompt)
                import re
                digest = re.search(r'"article_sha256":"([a-f0-9]{64})"', prompt).group(1)
                return {"schema":SCHEMA,"article_sha256":digest,"findings":[]}
            report, remote = review_once(
                client, 9768, {**complete_evidence(client.p),"asve_dossier":dossier},
                str(Path(root)/"private.db"), run_asve=True, asve_analyzer=analyzer
            )
            self.assertIsNone(remote)
            self.assertEqual(len(seen),1)
            self.assertEqual(report["secondary_analysis_status"],"NO_MATERIAL_FINDINGS")
            self.assertEqual(report["secondary_analysis"]["finding_count"],0)
            self.assertFalse(report["publication_authorized"])
            self.assertEqual(client.writes,[])

    def test_asve_opt_in_fails_closed_without_complete_source_dossier(self):
        with tempfile.TemporaryDirectory() as root:
            client=FakeWP()
            with self.assertRaisesRegex(ValueError,"asve_dossier"):
                review_once(client,9768,complete_evidence(client.p),
                            str(Path(root)/"private.db"),run_asve=True)
            self.assertEqual(client.writes,[])

    def test_published_pages_catalog_uses_only_valid_published_same_site_rows(self):
        client = object.__new__(WPClient)
        client.call = lambda *args: [
            {"id":12,"title":{"rendered":"Published page"},"link":"https://conexotech.com.br/a/","status":"publish"},
            {"id":13,"title":{"rendered":"Draft"},"link":"https://conexotech.com.br/b/","status":"draft"},
            {"id":"bad","title":"Bad ID","link":"https://conexotech.com.br/c/","status":"publish"},
        ]
        pages=client.published_pages()
        self.assertEqual(len(pages),4)
        from mkt_flow_p0.editorial_secondary_analysis import build_analysis_request
        request=build_analysis_request("Texto",{"sources":[],"claims":[]},pages)
        self.assertEqual(request["allowed_internal_page_ids"],["page:12","post:12"])

    def test_wp_executor_registers_p2_only_after_version_recheck(self):
        from mkt_flow_p0.editorial_secondary_analysis import SCHEMA
        from mkt_flow_p0.fila_pautas import listar_topicos_asve
        with tempfile.TemporaryDirectory() as root:
            client=FakeWP()
            dossier={
                "sources":[{
                    "source_id":"s1","url":"https://www.epe.gov.br/pde","publisher":"EPE",
                    "source_type":"planning_document","source_role":"primary_origin",
                    "published_at":"2026-11-01","reference_period":"2026-2036",
                    "locator":"Caderno de demanda, tabela 1",
                    "methodology":"Cenário EPE publicado",
                    "limitations":"Projeção condicionada a premissas",
                    "retrieved_at":"2026-11-27T10:00:00Z"
                }],
                "claims":[{
                    "claim_id":"c1","claim_text":"A projeção aumenta.",
                    "source_ids":["s1"],"source_role":"primary_origin",
                    "verification_status":"PROJETADA"
                }]
            }
            def analyzer(prompt):
                import re
                digest=re.search(r'"article_sha256":"([a-f0-9]{64})"',prompt).group(1)
                return {"schema":SCHEMA,"article_sha256":digest,"findings":[{
                    "finding_id":"f-p2","priority":"P2","dimension":"conexoes_relevantes",
                    "location":"Conclusão","observation":"A confiabilidade de rede merece pauta própria.",
                    "reader_impact":"O aprofundamento amplia a cobertura sem alongar esta notícia.",
                    "evidence_refs":[],"claim_refs":[],"recommended_action":"Registrar pauta futura.",
                    "internal_page_refs":[],"future_topic":{
                        "title":"Confiabilidade elétrica de data centers",
                        "rationale":"Grandes cargas dependem de rede e disponibilidade.",
                        "research_question":"Como transmissão e armazenamento acompanham novas cargas?"
                    }
                }]}
            db=str(Path(root)/"reviews.db")
            queue=str(Path(root)/"queue.db")
            report,_=review_once(client,9768,{**complete_evidence(client.p),"asve_dossier":dossier},
                db,run_asve=True,asve_analyzer=analyzer,topic_db_path=queue,
                register_asve_topics=True)
            topics=listar_topicos_asve(db_path=queue)
            self.assertEqual(len(topics),1)
            self.assertEqual(topics[0]["origin_article_id"],"wp:9768")
            self.assertEqual(len(report["asve_future_topics_registered"]),1)
            self.assertEqual(report["secondary_analysis_status"],"P2_BACKLOG_ONLY")

    def test_wp_executor_does_not_register_p2_for_concurrently_changed_article(self):
        from mkt_flow_p0.editorial_secondary_analysis import SCHEMA
        with tempfile.TemporaryDirectory() as root:
            client=FakeWP(mutate=True)
            dossier={
                "sources":[{
                    "source_id":"s1","url":"https://www.epe.gov.br/pde","publisher":"EPE",
                    "source_type":"planning_document","source_role":"primary_origin",
                    "published_at":"2026-11-01","reference_period":"2026-2036",
                    "locator":"Caderno de demanda, tabela 1",
                    "methodology":"Cenário EPE publicado",
                    "limitations":"Projeção condicionada a premissas",
                    "retrieved_at":"2026-11-27T10:00:00Z"
                }],
                "claims":[{
                    "claim_id":"c1","claim_text":"A projeção aumenta.",
                    "source_ids":["s1"],"source_role":"primary_origin",
                    "verification_status":"PROJETADA"
                }]
            }
            def analyzer(prompt):
                import re
                digest=re.search(r'"article_sha256":"([a-f0-9]{64})"',prompt).group(1)
                return {"schema":SCHEMA,"article_sha256":digest,"findings":[{
                    "finding_id":"f-p2","priority":"P2","dimension":"conexoes_relevantes",
                    "location":"Conclusão","observation":"A rede merece aprofundamento.",
                    "reader_impact":"A pauta amplia o tema.",
                    "evidence_refs":[],"claim_refs":[],"recommended_action":"Registrar pauta.",
                    "internal_page_refs":[],"future_topic":{
                        "title":"Rede para data centers",
                        "rationale":"Tema adjacente de infraestrutura.",
                        "research_question":"Como atender novas cargas?"
                    }
                }]}
            queue=str(Path(root)/"queue.db")
            with self.assertRaisesRegex(WPReadError,"changed while reviewing"):
                review_once(client,9768,{**complete_evidence(client.p),"asve_dossier":dossier},
                    str(Path(root)/"reviews.db"),run_asve=True,asve_analyzer=analyzer,topic_db_path=queue,
                    register_asve_topics=True)
            self.assertFalse(Path(queue).exists())


    def test_wp_executor_keeps_p2_suggestions_out_of_shared_queue_by_default(self):
        from mkt_flow_p0.editorial_secondary_analysis import SCHEMA
        with tempfile.TemporaryDirectory() as root:
            client=FakeWP()
            dossier={
                "sources":[{
                    "source_id":"s1","url":"https://www.epe.gov.br/pde","publisher":"EPE",
                    "source_type":"planning_document","source_role":"primary_origin",
                    "published_at":"2026-11-01","reference_period":"2026-2036",
                    "locator":"Caderno de demanda, tabela 1",
                    "methodology":"Cenário EPE publicado",
                    "limitations":"Projeção condicionada a premissas",
                    "retrieved_at":"2026-11-27T10:00:00Z"
                }],
                "claims":[{
                    "claim_id":"c1","claim_text":"A projeção aumenta.",
                    "source_ids":["s1"],"source_role":"primary_origin",
                    "verification_status":"PROJETADA"
                }]
            }
            def analyzer(prompt):
                import re
                digest=re.search(r'"article_sha256":"([a-f0-9]{64})"',prompt).group(1)
                return {"schema":SCHEMA,"article_sha256":digest,"findings":[{
                    "finding_id":"f-p2","priority":"P2","dimension":"conexoes_relevantes",
                    "location":"Conclusão","observation":"A rede merece aprofundamento.",
                    "reader_impact":"A pauta amplia a compreensão.",
                    "evidence_refs":[],"claim_refs":[],
                    "recommended_action":"Avaliar criação de matéria separada.",
                    "internal_page_refs":[],
                    "future_topic":{
                        "title":"Confiabilidade de redes elétricas",
                        "rationale":"A nova demanda exige planejamento de infraestrutura.",
                        "research_question":"Como a rede pode atender data centers?"
                    }
                }]}
            queue=str(Path(root)/"shared-queue.db")
            report,_=review_once(
                client,9768,{**complete_evidence(client.p),"asve_dossier":dossier},
                str(Path(root)/"reviews.db"),run_asve=True,asve_analyzer=analyzer,
                topic_db_path=queue
            )
            self.assertFalse(Path(queue).exists())
            self.assertNotIn("asve_future_topics_registered",report)
            self.assertEqual(report["secondary_analysis_status"],"P2_BACKLOG_ONLY")


    def test_published_content_catalog_includes_posts_and_pages(self):
        client=object.__new__(WPClient)
        calls=[]
        def call(method,path):
            calls.append(path)
            return [{"id":20,"title":{"rendered":"Published"},"link":"https://conexotech.com.br/published/","status":"publish"}]
        client.call=call
        catalog=client.published_pages(limit=75)
        self.assertEqual({item["content_type"] for item in catalog},{"post","page"})
        self.assertIn("wp/v2/posts?",calls[0])
        self.assertIn("wp/v2/pages?",calls[1])
        self.assertEqual({item["page_id"] for item in catalog},{"post:20","page:20"})

    def test_incomplete_published_content_catalog_fails_closed(self):
        client=object.__new__(WPClient)
        def call(method,path):
            if "page=6" in path:
                return [{"id":501}]
            return [{"id":i,"title":"Published","link":"https://conexotech.com.br/a/","status":"publish"}
                    for i in range(1,101)]
        client.call=call
        with self.assertRaisesRegex(WPReadError,"exceeds configured cap"):
            client.published_pages(limit=500)



if __name__ == "__main__":
    unittest.main()
