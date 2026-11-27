import unittest

from mkt_flow_p0.editorial_secondary_analysis import (
    SCHEMA, RECEIPT_SCHEMA, build_analysis_request, validate_analysis_result,
    validate_dispositions, run_secondary_analysis, attach_to_unique_reviewer,
)


def dossier():
    return {
        "sources": [
            {"source_id": "s1", "url": "https://www.epe.gov.br/pde",
             "publisher": "EPE", "source_type": "planning_document",
             "source_role": "primary_origin", "published_at": "2026-11-01",
             "reference_period": "2026-2036", "locator": "Caderno de demanda, tabela 1",
             "methodology": "Cenário de referência publicado pela EPE",
             "limitations": "Projeção condicionada a premissas, não medição",
             "retrieved_at": "2026-11-27T10:00:00Z"},
            {"source_id": "s2", "url": "https://dados.ons.org.br/",
             "publisher": "ONS", "source_type": "system_operator_data",
             "source_role": "independent_measurement", "published_at": "2026-11-01",
             "reference_period": "2026-11", "locator": "Dataset de carga, campo horário",
             "methodology": "Série de operação consolidada do ONS",
             "limitations": "Sujeita à revisão operacional; não é projeção",
             "retrieved_at": "2026-11-27T10:00:00Z"},
        ],
        "claims": [
            {"claim_id": "c1", "claim_text": "A demanda projetada cresce.",
             "source_ids": ["s1"], "source_role": "primary_origin",
             "verification_status": "PROJETADA"}
        ],
    }


def pages():
    return [
        {"page_id": "p1", "title": "Redes elétricas", "url": "https://conexotech.com.br/redes-eletricas/",
         "status": "publish"},
        {"page_id": "p2", "title": "Rascunho", "url": "https://conexotech.com.br/rascunho/",
         "status": "draft"},
        {"page_id": "p3", "title": "Outro domínio", "url": "https://example.com/noticia/",
         "status": "publish"},
    ]


def finding(priority="P1"):
    return {
        "finding_id": "f1", "priority": priority, "dimension": "contrapontos_e_limitacoes",
        "location": "Seção sobre projeções",
        "observation": "A estimativa não explicita sua premissa de crescimento.",
        "reader_impact": "O leitor pode interpretar o cenário como previsão garantida.",
        "evidence_refs": ["s1"], "claim_refs": ["c1"],
        "recommended_action": "Verificar o cenário e atribuir a projeção com suas premissas.",
        "internal_page_refs": ["p1"] if priority == "P1" else [],
        "future_topic": None if priority != "P2" else {
            "title": "Como as redes elétricas acompanham novas cargas",
            "rationale": "A infraestrutura merece aprofundamento próprio.",
            "research_question": "Quais investimentos de rede estão previstos?"
        },
    }


class RequestTests(unittest.TestCase):
    def test_request_hash_and_published_internal_pages_only(self):
        req = build_analysis_request("# Título\n\nTexto.", dossier(), pages())
        self.assertEqual(req["schema"], SCHEMA)
        self.assertEqual(len(req["article_sha256"]), 64)
        self.assertEqual(req["allowed_internal_page_ids"], ["p1"])
        self.assertNotIn("primary_review", req)
        self.assertIn("não reescreva", req["prompt"].lower())

    def test_invalid_internal_url_never_becomes_allowlisted(self):
        bad = [{"page_id":"bad","title":"Fake","url":"http://conexotech.com.br/a","status":"publish"}]
        req = build_analysis_request("Artigo.", dossier(), bad)
        self.assertEqual(req["allowed_internal_page_ids"], [])

    def test_no_article_or_invalid_dossier_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "ARTICLE_EMPTY"):
            build_analysis_request(" ", dossier(), [])
        with self.assertRaisesRegex(ValueError, "EVIDENCE_DOSSIER_INVALID"):
            build_analysis_request("Texto", None, [])


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.article = "Artigo sobre energia e data centers."
        self.request = build_analysis_request(self.article, dossier(), pages())

    def test_zero_findings_is_valid(self):
        result = {"schema": SCHEMA, "article_sha256": self.request["article_sha256"], "findings": []}
        receipt = validate_analysis_result(result, self.request)
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], "NO_MATERIAL_FINDINGS")
        self.assertFalse(receipt["publication_authorized"])

    def test_valid_p1_is_accepted_as_advisory_finding(self):
        result = {"schema": SCHEMA, "article_sha256": self.request["article_sha256"], "findings": [finding()]}
        receipt = validate_analysis_result(result, self.request)
        self.assertEqual(receipt["finding_count"], 1)
        self.assertFalse(receipt["rewrote_article"])

    def test_p2_requires_future_topic_and_does_not_block(self):
        result = {"schema": SCHEMA, "article_sha256": self.request["article_sha256"], "findings": [finding("P2")]}
        receipt = validate_analysis_result(result, self.request)
        self.assertEqual(receipt["findings"][0]["priority"], "P2")

    def test_wrong_version_or_unknown_reference_rejected(self):
        wrong = {"schema": SCHEMA, "article_sha256": "0"*64, "findings": []}
        with self.assertRaisesRegex(ValueError, "VERSION_MISMATCH"):
            validate_analysis_result(wrong, self.request)
        bad = finding()
        bad["evidence_refs"] = ["invented"]
        with self.assertRaisesRegex(ValueError, "UNKNOWN_EVIDENCE"):
            validate_analysis_result({"schema":SCHEMA,"article_sha256":self.request["article_sha256"],"findings":[bad]},self.request)

    def test_rewrite_and_sixth_finding_rejected(self):
        bad = finding()
        bad["rewritten_article"] = "texto"
        with self.assertRaisesRegex(ValueError, "REWRITE"):
            validate_analysis_result({"schema":SCHEMA,"article_sha256":self.request["article_sha256"],"findings":[bad]},self.request)
        six = [dict(finding(), finding_id=f"f{i}") for i in range(6)]
        with self.assertRaisesRegex(ValueError, "FINDINGS_LIMIT"):
            validate_analysis_result({"schema":SCHEMA,"article_sha256":self.request["article_sha256"],"findings":six},self.request)

    def test_material_finding_without_claim_or_evidence_rejected(self):
        bad=finding();bad["evidence_refs"]=[];bad["claim_refs"]=[]
        with self.assertRaisesRegex(ValueError, "WITHOUT_EVIDENCE"):
            validate_analysis_result({"schema":SCHEMA,"article_sha256":self.request["article_sha256"],"findings":[bad]},self.request)


class DecisionTests(unittest.TestCase):
    def test_p0_requires_incorporation_and_hash_bound_decision(self):
        article="Artigo."
        req=build_analysis_request(article,dossier(),[])
        f=finding("P0");f["internal_page_refs"]=[]
        receipt=validate_analysis_result({"schema":SCHEMA,"article_sha256":req["article_sha256"],"findings":[f]},req)
        pending=validate_dispositions(receipt,[])
        self.assertEqual(pending["status"],"DECISIONS_PENDING")
        decision={"finding_id":"f1","article_sha256":req["article_sha256"],"disposition":"incorporated"}
        closed=validate_dispositions(receipt,[decision])
        self.assertEqual(closed["status"],"CLOSED")
        self.assertFalse(closed["publication_authorized"])

    def test_p1_rejection_requires_reason(self):
        req=build_analysis_request("Artigo.",dossier(),pages())
        receipt=validate_analysis_result({"schema":SCHEMA,"article_sha256":req["article_sha256"],"findings":[finding()]},req)
        no_reason={"finding_id":"f1","article_sha256":req["article_sha256"],"disposition":"rejected_with_reason"}
        self.assertEqual(validate_dispositions(receipt,[no_reason])["status"],"DECISIONS_PENDING")
        no_reason["rationale"]="O ponto foi considerado não material nesta pauta."
        self.assertEqual(validate_dispositions(receipt,[no_reason])["status"],"CLOSED")

    def test_attach_does_not_overwrite_primary_reviewer_verdict(self):
        article="Artigo."
        req=build_analysis_request(article,dossier(),[])
        receipt=validate_analysis_result({"schema":SCHEMA,"article_sha256":req["article_sha256"],"findings":[]},req)
        primary={"veredito":"REVISAO_NECESSARIA","publicacao_autorizada":False}
        combined=attach_to_unique_reviewer(primary,receipt,article)
        self.assertEqual(combined["veredito"],"REVISAO_NECESSARIA")
        self.assertFalse(combined["publication_authorized"])
        with self.assertRaisesRegex(ValueError,"VERSION_MISMATCH"):
            attach_to_unique_reviewer(primary,receipt,article+" alterado")

    def test_analyzer_is_injected_and_receives_only_independent_prompt(self):
        captured={}
        def analyzer(prompt):
            captured["prompt"]=prompt
            return {"schema":SCHEMA,"article_sha256":self_digest,"findings":[]}
        req=build_analysis_request("Artigo.",dossier(),[])
        self_digest=req["article_sha256"]
        receipt=run_secondary_analysis("Artigo.",dossier(),[],analyzer)
        self.assertEqual(receipt["status"],"NO_MATERIAL_FINDINGS")
        self.assertNotIn("parecer da primeira revisão",captured["prompt"].lower())

    def test_p2_without_owner_disposition_does_not_keep_other_decisions_open(self):
        req=build_analysis_request("Artigo.",dossier(),[])
        p1=finding("P1")
        p1["internal_page_refs"]=[]
        p2=finding("P2")
        p2["finding_id"]="f2"
        p2["evidence_refs"]=[]
        p2["claim_refs"]=[]
        p2["internal_page_refs"]=[]
        receipt=validate_analysis_result({
            "schema":SCHEMA,"article_sha256":req["article_sha256"],
            "findings":[p1,p2]
        },req)
        decision={"finding_id":"f1","article_sha256":req["article_sha256"],
                  "disposition":"accepted_with_reason",
                  "rationale":"O contexto já está apresentado."}
        outcome=validate_dispositions(receipt,[decision])
        self.assertEqual(outcome["status"],"CLOSED")
        self.assertEqual(outcome["unresolved_findings"],[])



if __name__ == "__main__":
    unittest.main()
