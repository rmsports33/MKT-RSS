import unittest

from mkt_flow_p0.editorial_secondary_analysis import SCHEMA, build_analysis_request, validate_analysis_result
from mkt_flow_p0.revisor_qualidade_unico import (
    incorporar_analise_secundaria, executar_revisao_com_asve,
)


def data():
    article = "Artigo sobre energia e data centers."
    dossier = {
        "sources": [{"source_id":"s1","url":"https://www.epe.gov.br/pde","publisher":"EPE",
                     "source_type":"planning_document","source_role":"primary_origin",
                     "published_at":"2026-11-01","reference_period":"2026-2036",
                     "locator":"Caderno de demanda, tabela 1",
                     "methodology":"Cenário de referência publicado pela EPE",
                     "limitations":"Projeção condicionada a premissas, não medição",
                     "retrieved_at":"2026-11-27T10:00:00Z"}],
        "claims": [{"claim_id":"c1","claim_text":"Projeção","source_ids":["s1"],
                    "source_role":"primary_origin","verification_status":"PROJETADA"}],
    }
    return article, dossier


def make_receipt(priority):
    article, dossier = data()
    request = build_analysis_request(article, dossier, [])
    finding = {
        "finding_id": "f1", "priority": priority, "dimension": "contrapontos_e_limitacoes",
        "location": "Projeção",
        "observation": "A premissa não está apresentada.",
        "reader_impact": "O cenário pode parecer certeza.",
        "evidence_refs": ["s1"], "claim_refs": ["c1"],
        "recommended_action": "Expor a premissa e o horizonte.",
        "internal_page_refs": [],
        "future_topic": ({
            "title":"Redes elétricas", "rationale":"Tema adjacente.",
            "research_question":"Quais reforços de rede são necessários?"
        } if priority == "P2" else None),
    }
    return article, validate_analysis_result(
        {"schema":SCHEMA,"article_sha256":request["article_sha256"],"findings":[finding]},
        request
    )


class UniqueReviewerASVETests(unittest.TestCase):
    def test_p0_blocks_unique_reviewer_verdict(self):
        article, receipt = make_receipt("P0")
        main = {"veredito":"APTO_PARA_APROVACAO","pendencias":[]}
        result = incorporar_analise_secundaria(main, article, receipt)
        self.assertEqual(result["veredito_revisao_principal"],"APTO_PARA_APROVACAO")
        self.assertEqual(result["veredito"],"REVISAO_NECESSARIA")
        self.assertEqual(result["secondary_analysis_status"],"EDITORIAL_DECISION_REQUIRED")
        self.assertFalse(result["publication_authorized"])

    def test_p1_requires_a_version_bound_decision(self):
        article, receipt = make_receipt("P1")
        main = {"veredito":"APTO_PARA_APROVACAO","pendencias":[]}
        without = incorporar_analise_secundaria(main,article,receipt)
        self.assertEqual(without["veredito"],"REVISAO_NECESSARIA")
        decision = {"finding_id":"f1","article_sha256":receipt["article_sha256"],
                    "disposition":"rejected_with_reason",
                    "rationale":"O ponto não altera a conclusão nem o escopo desta matéria."}
        closed = incorporar_analise_secundaria(main,article,receipt,[decision])
        self.assertEqual(closed["veredito"],"APTO_PARA_APROVACAO")
        self.assertEqual(closed["secondary_analysis_status"],"DECISIONS_RECORDED")

    def test_p2_goes_to_backlog_without_blocking(self):
        article, receipt = make_receipt("P2")
        main = {"veredito":"APTO_PARA_APROVACAO","pendencias":[]}
        result = incorporar_analise_secundaria(main,article,receipt)
        self.assertEqual(result["veredito"],"APTO_PARA_APROVACAO")
        self.assertEqual(result["secondary_analysis_status"],"P2_BACKLOG_ONLY")

    def test_combined_orchestrator_uses_injected_independent_analyzer(self):
        article, dossier = data()
        called = []
        def analyzer(prompt):
            called.append(prompt)
            request = build_analysis_request(article, dossier, [])
            return {"schema": SCHEMA, "article_sha256": request["article_sha256"], "findings": []}
        main = {"veredito":"APTO_PARA_APROVACAO","pendencias":[]}
        result = executar_revisao_com_asve(main, article, dossier, [], analyzer=analyzer)
        self.assertEqual(len(called), 1)
        self.assertEqual(result["review"]["secondary_analysis_status"], "NO_MATERIAL_FINDINGS")
        self.assertFalse(result["publication_authorized"])
        self.assertTrue(result["analyzer_injected_by_orchestrator"])
        self.assertFalse(result["existing_provider_invoked")


if __name__ == "__main__":
    unittest.main()
