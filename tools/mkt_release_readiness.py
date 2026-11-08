"""Non-mutating readiness probe using the existing executor's credentials.

One deliberately INVALID broker request (post_id=0) confirms the caller passes
the allowlist and reaches contract validation. Reviewed RC3 rejects it before
snapshot, signing, reservation or any write. Never accepts article/intent input.
"""
import json
import os
import re
import requests

from tools.wp_identity_preflight import check_identity, SITE
from mkt_flow_p0.editorial_trace_turso import get_turso_trace

PROOF_RUN = "707b82b8-0e56-4bb7-9bbc-935efeda117d"
HOST = "mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io"


def probe(environ, *, session=requests, identity_check=check_identity,
          trace_read=get_turso_trace):
    report = {"identity": identity_check(environ), "writes_authorized": False,
              "publication_authorized": False, "signed_seo_broker_supported": False}
    if report["identity"] != "PASS":
        return report
    auth = (environ["WP_USER"], environ["WP_APP_PASSWORD"])

    def call(method, path, **kwargs):
        try:
            reply = session.request(method, SITE + path, auth=auth, timeout=15,
                                    allow_redirects=False, **kwargs)
            if len(reply.content) > 512 * 1024:
                return None, None
            data = reply.json()
            return reply.status_code, data if isinstance(data, dict) else None
        except (requests.RequestException, ValueError):
            return None, None

    status, body = call("POST", "/wp-json/conexo/v1/editorial/broker/write",
                        json={"executor": "mkt_rss", "post_id": 0})
    report["broker_allowlist"] = "PASS" if (
        status == 422 and body and body.get("code") == "conexo_editorial_blocked"
        and body.get("message") == "Contrato de publicacao invalido."
    ) else "BLOCKED"
    report["broker_http_status"] = status

    status, body = call("GET", "/wp-json/conexo/v1/editorial/snapshot/9768")
    snap = body.get("snapshot") if body else None
    sha = body.get("snapshot_sha256") if body else None
    valid = (status == 200 and isinstance(snap, dict) and snap.get("ID") == 9768
             and isinstance(sha, str) and re.fullmatch(r"[a-f0-9]{64}", sha))
    report["candidate_snapshot"] = "PASS" if valid else "BLOCKED"
    if valid:
        report["candidate_status"] = snap.get("post_status") if snap.get("post_status") in ("draft", "pending", "publish", "future", "private") else "UNKNOWN"
        report["candidate_author_id"] = snap.get("post_author") if type(snap.get("post_author")) is int else None
        report["candidate_snapshot_sha256"] = sha
        report["candidate_author_cannot_approve"] = True

    status, body = call("GET", "/wp-json/conexo/v1/editorial/seo-readiness")
    valid = status == 200 and body and body.get("schema") == "conexo-seo-readiness/1"
    report["seo_readiness_read"] = "PASS" if valid else "BLOCKED"
    report["signed_seo_broker_supported"] = bool(valid and body.get("broker_signed_seo_supported") is True)
    for flag in ("editorial_gate_ready", "seo_signing_ready", "seo_public_output_ready"):
        report[flag] = body.get(flag) is True if valid else False
    report["strict_seo_ready"] = all(report.get(key) is True for key in (
        "signed_seo_broker_supported", "editorial_gate_ready", "seo_signing_ready", "seo_public_output_ready"))

    # Read only the previously homologated synthetic row. Never fabricate a
    # release trace, PASS stage, human decision, or article-specific approval.
    if (environ.get("TURSO_DATABASE_URL") == "libsql://" + HOST
            and environ.get("CONEXO_TRACE_TURSO_ALLOWED_HOST") == HOST
            and environ.get("TURSO_AUTH_TOKEN", "").strip()):
        result = trace_read(PROOF_RUN)
        trace = result.get("trace") if isinstance(result, dict) else None
        report["turso_homolog_read"] = "PASS" if (
            isinstance(result, dict) and result.get("ok") is True and isinstance(trace, dict)
            and trace.get("run_id") == PROOF_RUN
            and trace.get("publication_authorized") is False
        ) else "BLOCKED"
    else:
        report["turso_homolog_read"] = "NOT_CONFIGURED"
    report["article_approval"] = "NOT_VERIFIED"
    return report


def main():
    report = probe(os.environ)
    text = json.dumps(report, sort_keys=True)
    print(text)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write("MKT-RSS technical preflight; no article writes or approval.\n\n```json\n" + text + "\n```\n")
    checks = ("identity", "broker_allowlist", "candidate_snapshot", "seo_readiness_read", "turso_homolog_read")
    return 0 if all(report.get(key) == "PASS" for key in checks) and report.get("strict_seo_ready") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
