import copy
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from mkt_flow_p0.opportunities import demand_report, evaluate, instant, load_candidates

NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)


def candidate():
    return {"title": "EXEMPLO SINTETICO: comparar celular", "url": "https://example.org/a",
        "kind": "review", "observed_at": NOW.isoformat(),
        "products": [{"model": "modelo-sintetico", "variant": "256GB", "market": "BR",
            "source_url": "https://example.org/model", "checked_at": NOW.isoformat(),
            "commercial_status": "active", "support_status": "active", "available_new": True}],
        "evidence": [{"claim": "Exemplo, nao e um fato de produto", "nature": "official",
            "source_url": "https://example.org/model", "locator": "secao exemplo",
            "checked_at": NOW.isoformat()}],
        "demand": {"source": "trends", "geo": "BR", "source_url": "https://trends.google.com/",
            "period_start": (NOW - timedelta(days=7)).isoformat(), "period_end": NOW.isoformat(),
            "observed_at": NOW.isoformat(), "comparison_group": "synthetic-1",
            "points": [{"at": (NOW - timedelta(days=7-i)).isoformat(), "value": 20+i}
                       for i in range(7)]}}


class OpportunitiesTests(unittest.TestCase):
    def test_complete_evidence_is_only_candidate_never_publication(self):
        r = evaluate(candidate(), now=NOW)
        self.assertEqual(r["status"], "CANDIDATA_A_REVISAO")
        self.assertFalse(r["publication_authorized"])
        self.assertFalse(r["factuality_verified"])
        self.assertIsNone(r["demand"]["market_search_volume"])

    def test_discontinued_product_overrides_positive_demand(self):
        c = candidate()
        c["products"][0]["commercial_status"] = "discontinued"
        r = evaluate(c, now=NOW)
        self.assertEqual(r["status"], "DESCARTAR")
        self.assertIn("PRODUTO_FORA_DA_SELECAO_COMERCIAL", r["reasons"])

    def test_age_of_model_alone_does_not_imply_end_of_support(self):
        c = candidate()
        c["products"][0]["release_at"] = "2020-01-01T00:00:00Z"
        self.assertEqual(evaluate(c, now=NOW)["status"], "CANDIDATA_A_REVISAO")

    def test_unknown_support_not_accepted(self):
        c = candidate()
        c["products"][0]["support_status"] = "unknown"
        self.assertIn("SUPORTE_DESCONHECIDO", evaluate(c, now=NOW)["reasons"])

    def test_each_comparison_model_must_be_eligible(self):
        c = candidate()
        c["kind"] = "comparativo"
        c["products"].append(dict(c["products"][0], model="second", commercial_status="residual"))
        self.assertEqual(evaluate(c, now=NOW)["status"], "DESCARTAR")

    def test_news_publication_does_not_refresh_old_event(self):
        c = candidate()
        c.update(kind="noticia", published_at=NOW.isoformat(),
                 event_at=(NOW-timedelta(days=8)).isoformat())
        self.assertIn("FATO_FORA_DOS_7_DIAS_OU_SEM_DATA", evaluate(c, now=NOW)["reasons"])

    def test_future_news_and_unknown_dates_fail_closed(self):
        for t in (None, "invalid", (NOW+timedelta(days=1)).isoformat()):
            c = candidate()
            c.update(kind="noticia", published_at=t, event_at=t)
            self.assertEqual(evaluate(c, now=NOW)["status"], "DESCARTAR")

    def test_expired_news_not_high_priority(self):
        c = candidate()
        c.update(kind="noticia", published_at=(NOW-timedelta(hours=49)).isoformat(), event_at=NOW.isoformat())
        self.assertIn("NOTICIA_PERDEU_JANELA_OU_SEM_DATA", evaluate(c, now=NOW)["reasons"])

    def test_offer_needs_recent_real_positive_price(self):
        c = candidate()
        c["kind"] = "oferta"
        for price in (0, -1, True, float("nan")):
            c["offer"] = {"price": price, "currency": "BRL", "url": c["url"], "checked_at": NOW.isoformat()}
            self.assertIn("OFERTA_SEM_PRECO_VALIDO_RECENTE", evaluate(c, now=NOW)["reasons"])
        c["offer"]["price"] = 100
        self.assertEqual(evaluate(c, now=NOW)["status"], "CANDIDATA_A_REVISAO")
        c["offer"]["checked_at"] = (NOW-timedelta(hours=7)).isoformat()
        self.assertIn("OFERTA_SEM_PRECO_VALIDO_RECENTE", evaluate(c, now=NOW)["reasons"])

    def test_five_day_tail_cannot_claim_seven_day_coverage(self):
        d = candidate()["demand"]
        d["points"] = d["points"][-5:]
        self.assertEqual(demand_report(d, NOW)["status"], "NAO_VERIFICADA")

    def test_autocomplete_is_not_demand(self):
        d = candidate()["demand"]
        d["source"] = "autocomplete"
        self.assertEqual(demand_report(d, NOW)["reason"], "SUGESTAO_NAO_MEDE_DEMANDA")

    def test_partial_missing_future_and_invalid_demand_are_unknown(self):
        for mutation in (lambda d: d["points"][0].update(partial=True),
                         lambda d: d.update(observed_at=(NOW+timedelta(hours=1)).isoformat()),
                         lambda d: d["points"][0].update(value=101),
                         lambda d: d.update(period_start=(NOW-timedelta(days=5)).isoformat())):
            d = candidate()["demand"]
            mutation(d)
            self.assertEqual(demand_report(d, NOW)["status"], "NAO_VERIFICADA")

    def test_missing_data_does_not_imply_zero_demand(self):
        c = candidate()
        c.pop("demand")
        r = evaluate(c, now=NOW)
        self.assertEqual(r["status"], "REVISAO_PENDENTE")
        self.assertEqual(r["demand"]["status"], "NAO_VERIFICADA")

    def test_evidence_without_claim_origin_is_not_complete(self):
        c = candidate()
        c["evidence"][0].pop("locator")
        self.assertIn("EVIDENCIA_INCOMPLETA", evaluate(c, now=NOW)["reasons"])

    def test_timezone_required_and_rfc822_supported(self):
        with self.assertRaises(ValueError):
            instant("2026-11-09T12:00:00")
        self.assertEqual(instant("Mon, 09 Nov 2026 09:00:00 -0300"), NOW)

    def test_import_export_survives_new_executor_without_ai_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            infile, outfile = root / "input.json", root / "report.json"
            infile.write_text(json.dumps([candidate()]), encoding="utf-8")
            script = Path(__file__).resolve().parents[1] / "editorial_opportunities.py"
            # -S removes installed packages. No credentials, network or AI SDK.
            command = [sys.executable, "-S", str(script), str(infile), "--now", NOW.isoformat(), "--output", str(outfile)]
            r = subprocess.run(command, capture_output=True, text=True, cwd=root)
            self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
            saved = json.loads(outfile.read_text())
            self.assertEqual(saved["items"][0]["status"], "CANDIDATA_A_REVISAO")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(json.loads(outfile.read_text()), saved)

    def test_csv_nested_evidence_is_portable(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "input.csv"
            c = candidate()
            row = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k,v in c.items()}
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            self.assertEqual(load_candidates(path), [c])


class CloudCollectionTests(unittest.TestCase):
    def test_missing_cloud_persistence_blocks_before_network(self):
        from rss_queue_collect import coletar
        with patch.dict("os.environ", {"CONEXO_REQUIRE_CLOUD_PERSISTENCE": "1"}, clear=True), \
             patch("rss_queue_collect.fetch_feed") as fetch:
            with self.assertRaisesRegex(RuntimeError, "PERSISTENCIA_CLOUD_AUSENTE"):
                coletar()
            fetch.assert_not_called()

    def test_old_and_undated_rss_not_registered(self):
        from rss_queue_collect import coletar
        with patch.dict("os.environ", {}, clear=True), \
             patch("rss_queue_collect.fetch_feed", return_value={"itens": [
                 {"titulo": "Old", "published": "2020-01-01T00:00:00Z"},
                 {"titulo": "Unknown", "published": ""}]}), \
             patch("rss_queue_collect.registrar") as register:
            r = coletar("tecnoblog", 2)
            self.assertEqual(r["fora_da_janela"], 2)
            register.assert_not_called()


if __name__ == "__main__":
    unittest.main()
