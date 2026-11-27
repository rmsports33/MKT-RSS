import unittest
from copy import deepcopy

from mkt_flow_p0.editorial_secondary_analysis import SCHEMA, build_analysis_request, validate_analysis_result
from mkt_flow_p0.editorial_gate_traceability import (
    SCHEMA as TRACE_SCHEMA,
    build_gate_traceability_sidecar,
    validate_gate_traceability_sidecar,
)


def dossier():
    return {
        "sources": [{
            "source_id":"s1","url":"https://www.epe.gov.br/pde","publisher":"EPE",
            "source_type":"planning_document","source_role":"primary_origin",
            "published_at":"2026-11-01","reference_period":"2026-2036",
            "locator":"Caderno de demanda, tabela 1",
            "methodology":"Cenário de referência publicado pela EPE",
            "limitations":"Projeção condicionada a premissas, não medição",
            "retrieved_at":"2026-11-27T10:00:00Z"
        }],
        "claims": [{
            "claim_id":"c1","claim_text":"A EPE projeta crescimento da demanda.",
            "source_ids":["s1"],"source_role":"primary_origin",
            "verification_status":"PROJETADA"
        }]
    }


def make_receipt(article, finding=None):
    request=build_analysis_request(article,dossier(),[])
    return validate_analysis_result({
        "schema":SCHEMA,
        "article_sha256":request["article_sha256"],
        "findings":[] if finding is None else [finding]
    },request)


def finding(priority):
    return {
        "finding_id":"f1","priority":priority,"dimension":"contrapontos_e_limitacoes",
        "location":"Seção de projeções",
        "observation":"O cenário depende de premissa que precisa ficar explícita.",
        "reader_impact":"O leitor pode interpretar uma projeção condicionada como resultado garantido.",
        "evidence_refs":["s1"],"claim_refs":["c1"],
        "recommended_action":"Explicitar a premissa e a incerteza.",
        "internal_page_refs":[],
        "future_topic":({
            "title":"Confiabilidade das redes elétricas",
            "rationale":"A expansão de data centers depende de transmissão e estabilidade.",
            "research_question":"Como redes e armazenamento acompanham as novas cargas?"
        } if priority=="P2" else None)
    }


class GateTraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.article="# IA e energia\n\nArtigo de teste."
        self.primary={"veredito":"APTO_PARA_APROVACAO","checks":{"fontes":"VERIFICADO"}}
        self.pages=[]

    def build(self, receipt, decisions=None, evidence=None):
        return build_gate_traceability_sidecar(
            self.article,evidence or dossier(),self.primary,receipt,self.pages,decisions or []
        )

    def test_empty_asve_is_valid_and_creates_non_authorizing_sidecar(self):
        receipt=make_receipt(self.article)
        sidecar=self.build(receipt)
        checked=validate_gate_traceability_sidecar(sidecar)
        self.assertEqual(sidecar["schema"],TRACE_SCHEMA)
        self.assertEqual(checked["handoff_status"],"TRACEABILITY_COMPLETE_FOR_GATE_CONSUMER")
        self.assertEqual(checked["gate_acceptance"],"NOT_IMPLEMENTED_IN_CXEG_PACKAGE_V1")
        self.assertFalse(sidecar["publication_authorized"])
        self.assertFalse(sidecar["factuality_verified_by_sidecar"])

    def test_article_hash_mismatch_is_rejected(self):
        receipt=make_receipt(self.article)
        with self.assertRaisesRegex(ValueError,"VERSION_MISMATCH"):
            build_gate_traceability_sidecar(
                self.article+" changed",dossier(),self.primary,receipt,self.pages
            )

    def test_p0_remains_blocked_even_after_disposition(self):
        receipt=make_receipt(self.article,finding("P0"))
        sidecar=self.build(receipt,[
            {"finding_id":"f1","article_sha256":receipt["article_sha256"],"disposition":"incorporated"}
        ])
        self.assertEqual(sidecar["handoff_status"],"BLOCKED_P0_REQUIRES_NEW_ARTICLE_VERSION")

    def test_p1_needs_decision_before_traceability_completion(self):
        receipt=make_receipt(self.article,finding("P1"))
        pending=self.build(receipt)
        self.assertEqual(pending["handoff_status"],"EDITORIAL_DECISION_REQUIRED")
        decision={"finding_id":"f1","article_sha256":receipt["article_sha256"],
                  "disposition":"accepted_with_reason","rationale":"A premissa está explicada em outra seção."}
        closed=self.build(receipt,[decision])
        self.assertEqual(closed["handoff_status"],"TRACEABILITY_COMPLETE_FOR_GATE_CONSUMER")

    def test_p2_is_nonblocking_and_remains_a_future_topic(self):
        receipt=make_receipt(self.article,finding("P2"))
        sidecar=self.build(receipt)
        self.assertEqual(sidecar["handoff_status"],"TRACEABILITY_COMPLETE_FOR_GATE_CONSUMER")
        self.assertEqual(sidecar["asve_finding_ids"]["P2"],["f1"])

    def test_tampering_sidecar_is_detected(self):
        sidecar=self.build(make_receipt(self.article))
        changed=deepcopy(sidecar)
        changed["claim_ids"]=[]
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):
            validate_gate_traceability_sidecar(changed)

    def test_sidecar_never_claims_current_gate_compatibility(self):
        sidecar=self.build(make_receipt(self.article))
        changed=deepcopy(sidecar)
        changed["gate_contract_compatibility"]["current_gate_accepts_sidecar"]=True
        body={k:v for k,v in changed.items() if k!="sidecar_sha256"}
        import hashlib,json
        changed["sidecar_sha256"]=hashlib.sha256(
            json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest()
        with self.assertRaisesRegex(ValueError,"FALSE_GATE_COMPATIBILITY"):
            validate_gate_traceability_sidecar(changed)


if __name__=="__main__":
    unittest.main()
