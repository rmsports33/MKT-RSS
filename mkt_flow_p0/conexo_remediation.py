"""MKT-RSS ↔ Conexo Gate rc10.1 draft remediation client.

Use from the already-running authenticated MKT-RSS executor. No approval, cron,
Actions, image substitution, or publication. Read-only unless apply=True.
"""
import base64
import json
import os
from urllib.request import Request, urlopen

SITE = "https://conexotech.com.br"
QUEUE = "/wp-json/conexo/v1/editorial/remediation/queue"
EXCERPT = "/wp-json/conexo/v1/editorial/remediation/excerpt"


class RemediationError(RuntimeError):
    pass


def run_remediation(transport, *, apply=False, max_changes=10, only_post_id=None):
    queue = transport("GET", QUEUE, None)
    if not isinstance(queue, dict) or queue.get("schema") != "conexo-remediation/1":
        raise RemediationError("Unexpected Gate queue schema")
    items = queue.get("items")
    if not isinstance(items, list):
        raise RemediationError("Missing remediation items")
    output = []
    changes = 0
    for item in items:
        if not isinstance(item, dict) or type(item.get("post_id")) is not int:
            raise RemediationError("Invalid queue item")
        if only_post_id is not None and item["post_id"] != only_post_id:
            continue
        issues = item.get("issues")
        if not isinstance(issues, list):
            raise RemediationError("Missing issues")
        result = {"post_id": item["post_id"], "issues": issues, "state": "requires_review"}
        eligible = (item.get("automatic_correction_available") is True and
                    isinstance(item.get("excerpt_suggestion"), str) and
                    len(item["excerpt_suggestion"]) >= 80 and
                    isinstance(item.get("modified_gmt"), str) and
                    isinstance(item.get("content_sha256"), str) and
                    len(item["content_sha256"]) == 64)
        if eligible and apply and changes < max_changes:
            payload = {"post_id": item["post_id"],
                       "content_sha256": item["content_sha256"],
                       "modified_gmt": item["modified_gmt"]}
            answer = transport("POST", EXCERPT, payload)
            if not isinstance(answer, dict) or answer.get("saved") is not True or answer.get("status") not in ("draft", "pending"):
                result["state"] = "write_uncertain_stop"
                output.append(result)
                break
            changes += 1
            result["state"] = "draft_excerpt_saved"
            result["remaining_issues"] = answer.get("remaining_issues", [])
        elif eligible:
            result["state"] = "excerpt_suggested_no_write"
        output.append(result)
    return {"items": output, "writes": changes, "published": False,
            "approved": False, "requires_human_review": True}


def wordpress_transport():
    user = os.environ.get("CONEXO_WP_USER")
    password = os.environ.get("CONEXO_WP_APP_PASSWORD")
    if not user or not password:
        raise RemediationError("Authorized MKT-RSS service credentials absent")
    token = base64.b64encode((user + ":" + password).encode()).decode()

    def transport(method, path, payload):
        if path not in (QUEUE, EXCERPT) or method not in ("GET", "POST"):
            raise RemediationError("Endpoint not allowed")
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        request = Request(SITE + path, data=raw, method=method,
                          headers={"Authorization": "Basic " + token,
                                   "Content-Type": "application/json"})
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    return transport


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--post-id", type=int)
    parser.add_argument("--max-changes", type=int, default=10)
    args = parser.parse_args()
    result = run_remediation(wordpress_transport(), apply=args.apply,
                             max_changes=max(0, min(10, args.max_changes)),
                             only_post_id=args.post_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
