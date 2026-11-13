"""Sem rede: verifica reconciliação paginada e preservação da fila."""
import unittest
from scripts.catalog_turso_reconcile_readonly import reconcile

class ReconcileTests(unittest.TestCase):
    def test_matches_and_states(self):
        calls = []
        def fetch(sql, args):
            calls.append((sql,args))
            assert sql.strip().upper().startswith("SELECT ")
            return {"rows": [["Motorola Signature 27 recebe atualização", "DESCOBERTA"],
                             ["Motorola Signature 27 é anunciado", "EM_REVISAO"],
                             ["Novo roteador", "DESCOBERTA"]]}
        report = reconcile(fetch=fetch)
        self.assertEqual(report["total_rows"], 3)
        self.assertEqual(report["products"]["motorola-signature-27"]["pautas"], 2)
        self.assertEqual(report["duplicate_product_pauta_candidates"], 1)
        self.assertEqual(report["unmatched_rows"], 1)
        self.assertFalse(report["queue_modified"])
        self.assertTrue(all(sql.startswith("SELECT") for sql,_ in calls))

    def test_fails_closed_on_database_error(self):
        def fetch(sql, args):
            return {"erro": "secret or network failure"}
        with self.assertRaisesRegex(RuntimeError, "TURSO_READ_FAILED"):
            reconcile(fetch=fetch)

    def test_invalid_state_blocks(self):
        def fetch(sql, args):
            return {"rows": [["TCL C6K 65", "PUBLICADO"]]}
        with self.assertRaisesRegex(RuntimeError, "UNKNOWN_EDITORIAL_STATE"):
            reconcile(fetch=fetch)

if __name__ == "__main__":
    unittest.main()
