"""Operational regression: new manual tooling must not disable existing cron."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CloudWorkflowPreservationTests(unittest.TestCase):
    def test_existing_daily_does_not_require_new_financial_variable(self):
        workflow = (ROOT / ".github/workflows/daily.yml").read_text()
        self.assertIn('cron: "0 12 * * *"', workflow)
        self.assertNotIn("CONEXO_FREE_AUTOMATION_READY", workflow)
        self.assertNotIn("CONEXO_REQUIRE_CLOUD_PERSISTENCE", workflow)

    def test_new_manual_job_cannot_run_in_private_copy_or_create_paid_storage(self):
        workflow = (ROOT / ".github/workflows/opportunities-manual.yml").read_text()
        self.assertIn("github.event.repository.private == false", workflow)
        self.assertIn("inputs.free_usage_reviewed", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertNotIn("cache:", workflow)


if __name__ == "__main__":
    unittest.main()
