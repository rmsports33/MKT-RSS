"""Revisão integral: workflows e fail-closed por ambiente.

No network. Reads workflow YAML as text and asserts destination guards.
"""
import glob
import os
import unittest
from pathlib import Path

import yaml

from mkt_flow_p0.wp_destination import (
    DestinationBlocked, resolve, VALIDATION_ENVIRONMENT,
    CANONICAL_SITE, OPERATION_DRAFT, OPERATION_PUBLISH,
)

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"


class WorkflowClassificationTests(unittest.TestCase):

    def _load(self, name):
        return yaml.safe_load((WF / name).read_text(encoding="utf-8"))

    def test_rss_homolog_draft_is_blocked_before_any_wp_call(self):
        text = (WF / "rss-homolog-manual.yml").read_text(encoding="utf-8")
        self.assertIn("draft mode disabled", text)
        self.assertIn("has no WordPress destination", text)
        # Old production URL check must be gone from the validation preflight.
        self.assertNotIn('os.getenv("WP_URL", "").rstrip("/") != "https://conexotech.com.br"', text)

    def test_rss_homolog_has_no_wp_write_step_enabled(self):
        wf = self._load("rss-homolog-manual.yml")
        steps = wf["jobs"]["editorial"]["steps"]
        for step in steps:
            if "Stage" in step.get("name", "") or "plugin" in step.get("name", "").lower():
                self.assertEqual(step.get("if"), "${{ false }}",
                                 f"write step not disabled: {step['name']}")

    def test_production_publish_workflows_declare_explicit_mode(self):
        for name in ("publish-owner-approved-manual.yml",
                     "publish-owner-approved-batch-manual.yml",
                     "produce-bank-article-manual.yml"):
            with self.subTest(wf=name):
                text = (WF / name).read_text(encoding="utf-8")
                self.assertIn("WP_OPERATION_MODE: production", text)

    def test_production_mode_alone_does_not_authorize_in_validation_env(self):
        env = {
            "WP_OPERATION_MODE": "production",
            "GITHUB_ENVIRONMENT": VALIDATION_ENVIRONMENT,
            "WP_URL": CANONICAL_SITE,
            "WP_USER": "svc",
            "WP_APP_PASSWORD": "test",
        }
        with self.assertRaises(DestinationBlocked):
            resolve(OPERATION_PUBLISH, env=env)

    def test_no_workflow_uses_staging_wp_url(self):
        for path in glob.glob(str(WF / "*.yml")):
            text = Path(path).read_text(encoding="utf-8")
            self.assertNotIn("https://staging.conexotech.com.br/wp-json", text, path)

    def test_all_workflows_parse_as_yaml(self):
        for path in glob.glob(str(WF / "*.yml")):
            with self.subTest(wf=os.path.basename(path)):
                yaml.safe_load(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
