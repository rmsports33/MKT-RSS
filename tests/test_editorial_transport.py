"""Contraprovas offline: não usa credenciais, site, RSS externo ou LLM."""
import base64
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if not os.environ.get("CONEXO_TEST_CORE_ROOT"):
    raise unittest.SkipTest("Definir CONEXO_TEST_CORE_ROOT para executar os testes de integração fixados por hash")
CORE = Path(os.environ["CONEXO_TEST_CORE_ROOT"])
sys.path.insert(0,str(CORE / "tests"))
import test_editorial_package as fixtures
from mkt_flow_p0 import editorial_transport as transport
from mkt_flow_p0.wp_publisher import publicar_no_wordpress, executar_ferramenta_mcp
from editorial_publish_gate import authorize_publish
import pipeline_rss

KEY="synthetic-test-key-never-use-in-production-123"

class Response:
    def __init__(self,data,status=200):self.data,self.status_code=data,status
    def json(self):return self.data


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.EditorialV2Tests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.prepare_wordpress()
        self.p=self.f.p
        p=self.p["payload"]
        self.snapshot={"ID":9711,"post_type":"post","post_status":"draft","post_date_gmt":"2026-10-30 09:00:00",
            "post_title":p["title"],"post_content":p["content"],"post_excerpt":p["excerpt"],
            "post_name":p["slug"],"post_author":3,"post_category":[10],"meta_input":{"_thumbnail_id":9714}}
        self.key=patch.dict(os.environ,{"CONEXO_EDITORIAL_GATE_KEY":KEY})
        self.key.start();self.addCleanup(self.key.stop)

    def call(self,**kwargs):
        return transport.publish_package(self.p,core_root=CORE,wp_url=transport.SITE,
            wp_user="synthetic-user",wp_password="synthetic-password",actor_id=4,**kwargs)

    def post_mock(self,url,**kwargs):
        claim=json.loads(base64.urlsafe_b64decode(kwargs["json"]["receipt"]+"="*(-len(kwargs["json"]["receipt"])%4)))
        expected=claim["post"].copy();expected["ID"]=expected["ID"] or 9900;expected.setdefault("post_date_gmt",self.snapshot["post_date_gmt"])
        expected["post_category"]=sorted(expected["post_category"])
        self.snapshot=expected
        return Response({"post_id":expected["ID"],"status":expected["post_status"],"snapshot":expected,
            "nonce":claim["nonce"],"version_sha256":claim["version_sha256"],"intent":claim["intent"],
            "link":transport.SITE+"/?p="+str(expected["ID"])})

    def get_mock(self,*args,**kwargs):
        return Response({"snapshot":copy.deepcopy(self.snapshot),"link":transport.SITE+"/?p="+str(self.snapshot["ID"])})

    def test_complete_stage_goes_only_to_signed_endpoint_and_is_not_delivery(self):
        with patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=self.post_mock) as post:
            r=self.call(intent="stage")
        self.assertNotIn("erro",r,r);self.assertFalse(r["editorial_delivered"])
        self.assertEqual(r["status"],"draft")
        self.assertEqual(post.call_args.args[0],transport.SITE+"/wp-json/conexo/v1/editorial/write")

    def test_missing_substantive_review_blocks_all_network(self):
        del self.p["payload"]["substantive_review"]
        with patch.object(transport.requests,"get") as get,patch.object(transport.requests,"post") as post:
            self.assertIn("erro",self.call())
        get.assert_not_called();post.assert_not_called()

    def test_legacy_pass_and_draft_cannot_bypass(self):
        with patch.object(transport.requests,"get") as get,patch.object(transport.requests,"post") as post:
            for status in ("draft","publish"):
                r=publicar_no_wordpress("T","texto","PASS",transport.SITE,"u","p",status_desejado=status)
                self.assertIn("erro",r)
        get.assert_not_called();post.assert_not_called()

    def test_direct_mcp_write_never_contacts_server(self):
        with patch.object(transport.requests,"post") as post:
            for tool in ("create_review","create_comparativo","schedule_publish","unknown_write"):
                self.assertIn("erro",executar_ferramenta_mcp(transport.SITE,"u","p",tool))
        post.assert_not_called()

    def test_missing_key_blocks_before_snapshot(self):
        with patch.dict(os.environ,{"CONEXO_EDITORIAL_GATE_KEY":""}),patch.object(transport.requests,"get") as get:
            self.assertIn("erro",self.call())
        get.assert_not_called()

    def test_old_four_approval_flags_are_no_longer_authority(self):
        review={"veredito":"APROVADO","revisao_substantiva":True,"evidencias_verificadas":True,"aprovacao_atual":True}
        self.assertFalse(authorize_publish({},review)["autorizado"])

    def test_canonical_complete_package_can_authorize_transition(self):
        self.p["stage"]="ready";self.f.approve()
        p=self.p["payload"]
        post={"id":9711,"status":"draft","categories":[10],"featured_media":9714,
              "title":p["title"],"content":p["content"],"slug":p["slug"],
              "link":transport.SITE+"/?p=9711"}
        self.assertTrue(authorize_publish(post,package=self.p,core_root=CORE)["autorizado"])

    def test_legacy_wrapper_routes_reviewed_draft_to_signed_transport(self):
        p=self.p["payload"]
        with patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=self.post_mock) as post:
            r=publicar_no_wordpress(p["title"],p["content"],"PASS",transport.SITE,"u","p",pacote_editorial=self.p,core_root=CORE,actor_id=4)
        self.assertNotIn("erro",r,r);self.assertTrue(r["editorial_delivered"])
        self.assertEqual(post.call_args.args[0],transport.SITE+"/wp-json/conexo/v1/editorial/write")

    def test_core_hash_mutation_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/"scripts").mkdir()
            (root/"scripts/validate_editorial_package.py").write_text("# altered")
            with self.assertRaises(ValueError):transport.load_core(root)

    def test_timeout_retains_nonce_and_never_retries(self):
        with patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=transport.requests.Timeout) as post:
            r=self.call()
        self.assertIn("erro",r);self.assertEqual(len(r["nonce"]),32)
        self.assertFalse(r["retry_automatic"]);self.assertEqual(post.call_count,1)

    def test_unauthorized_publish_never_posts(self):
        with patch.object(transport.requests,"get") as get,patch.object(transport.requests,"post") as post:
            self.assertIn("erro",self.call(intent="publish",publication_reference="ordem sintética"))
        get.assert_not_called();post.assert_not_called()

    def test_authorized_publish_and_readback(self):
        self.p["stage"]="ready";self.f.approve()
        with patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=self.post_mock):
            r=self.call(intent="publish",publication_reference="ordem sintética")
        self.assertNotIn("erro",r,r);self.assertEqual(r["status"],"publish")

    def test_rss_source_must_match_apuration_before_transport(self):
        with patch.object(transport.requests,"get") as get,patch.object(transport.requests,"post") as post:
            r=pipeline_rss.processar_pacote_editorial(self.p,core_root=CORE,actor_id=4)
        self.assertIn("erro",r);get.assert_not_called();post.assert_not_called()

    def test_rss_final_handoff_uses_same_transport(self):
        self.p["payload"]["discovery"]={"pauta_id":"a"*32,"source_url":self.p["payload"]["sources"][0]["url"]}
        self.f.approve();self.snapshot["post_content"]=self.p["payload"]["content"]
        with patch.dict(os.environ,{"WP_URL":transport.SITE,"WP_USER":"u","WP_APP_PASSWORD":"synthetic"}),patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=self.post_mock):
            r=pipeline_rss.processar_pacote_editorial(self.p,core_root=CORE,actor_id=4)
        self.assertNotIn("erro",r,r);self.assertEqual(r["acao"],"staged_for_theme_review")

    def test_python_signer_to_php_server(self):
        runner=os.environ.get("CXEG_WASM_RUNNER")
        site=os.environ.get("CXEG_TEST_SITE_ROOT")
        if not runner or not site:self.skipTest("PHP runtime não configurado")
        def post_php(url,**kwargs):
            with tempfile.TemporaryDirectory() as folder:
                vector=Path(folder)/"vector.json"
                vector.write_text(json.dumps({"snapshot":self.snapshot,"envelope":kwargs["json"]},ensure_ascii=False))
                run=subprocess.run(["node",runner,str(Path(site)/"mu-plugins/conexo-editorial-gate.php"),str(Path(site)/"tests/editorial_bridge.php"),str(vector)],capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                result=json.loads(run.stdout);self.snapshot=result["snapshot"]
                return Response(result)
        with patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=post_php):
            result=self.call(intent="stage")
        self.assertNotIn("erro",result,result);self.assertEqual(result["status"],"draft")

    def test_completed_nonce_resumes_without_post(self):
        nonce="a"*32
        result={"post_id":9711,"status":"draft","snapshot":self.snapshot.copy(),
                "nonce":nonce,"version_sha256":self.p["version_sha256"],"intent":"stage"}
        with patch.object(transport.requests,"get",side_effect=[Response({"state":"COMPLETE","result":result}),self.get_mock()]),patch.object(transport.requests,"post") as post:
            r=self.call(intent="stage",operation_nonce=nonce)
        self.assertTrue(r["resumed"]);post.assert_not_called()

    def test_reserved_or_missing_nonce_never_creates_new_operation(self):
        with patch.object(transport.requests,"get",return_value=Response({"state":"RESERVED"})),patch.object(transport.requests,"post") as post:
            self.assertIn("erro",self.call(operation_nonce="b"*32))
        post.assert_not_called()

    def test_bad_intent_actor_or_site_never_calls_network(self):
        with patch.object(transport.requests,"get") as get,patch.object(transport.requests,"post") as post:
            self.assertIn("erro",self.call(intent="unknown"))
            self.assertIn("erro",transport.publish_package(self.p,core_root=CORE,wp_url=None,wp_user="u",wp_password="p",actor_id=4))
        get.assert_not_called();post.assert_not_called()

    def test_real_sqlite_discovery_to_supervised_signed_write(self):
        consumer_path=os.environ.get("CONEXO_TEST_DISCOVERY_CONSUMER")
        if not consumer_path:self.skipTest("Consumidor PR43 não configurado")
        from mkt_flow_p0.fila_pautas import registrar
        from mkt_flow_p0.conexo_discovery_adapter import exportar_candidatos
        spec=importlib.util.spec_from_file_location("discovery_consumer_fixture",consumer_path)
        consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
        url=self.p["payload"]["sources"][0]["url"]
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/"rss.sqlite"
            registered=registrar({"titulo":"Atualização Android de segurança", "link":url,"fonte":"fonte sintética"},db_path=db)
            packet=exportar_candidatos(db_path=db)
            inbox=consumer.validar_pacote(packet)
        self.assertFalse(inbox["publication_allowed"])
        self.assertEqual(inbox["items"][0]["state"],"AWAITING_FACT_CHECK")
        self.assertEqual(inbox["items"][0]["pauta_id"],registered["id"])
        # Fixture assume apuração/revisão apenas para testar transporte. O ranking
        # não gera aprovação: sem o pacote completo, o mesmo caminho é bloqueado.
        self.p["payload"]["discovery"]={"pauta_id":registered["id"],"source_url":url}
        self.f.approve()
        with patch.dict(os.environ,{"WP_URL":transport.SITE,"WP_USER":"u","WP_APP_PASSWORD":"synthetic"}),patch.object(transport.requests,"get",side_effect=self.get_mock),patch.object(transport.requests,"post",side_effect=self.post_mock):
            result=pipeline_rss.processar_pacote_editorial(self.p,core_root=CORE,actor_id=4)
        self.assertNotIn("erro",result,result)
        self.assertFalse(result["editorial_delivered"])


if __name__=="__main__":unittest.main()
