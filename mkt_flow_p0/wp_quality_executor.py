"""WordPress-first quality reviewer: authenticated read, private SQLite evidence, fail-closed.

Cloud executor CLI:
  python -m mkt_flow_p0.wp_quality_executor --post-id 9768 --evidence-file /secure/9768.json
No WP write unless --submit-quality; never publishes or approves a post.
Application Password and user from environment, never in logs/source.
"""
import argparse
import base64
import json
import hashlib
import re
import os
from pathlib import Path
import sqlite3
import stat
import sys
import urllib.parse
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone

from mkt_flow_p0.revisor_qualidade_unico import avaliar_artigo, verificar_versao


class WPReadError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Do not send the Application Password to a redirected endpoint.
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise WPReadError("WordPress redirect forbidden")


class WPClient:
    def __init__(self, site, username, app_password):
        parsed = urllib.parse.urlparse(site)
        if (parsed.scheme != "https" or parsed.hostname != "conexotech.com.br"
                or parsed.username or parsed.password or parsed.path not in ("", "/")
                or parsed.query or parsed.fragment or parsed.port not in (None, 443)):
            raise ValueError("WP site must be the authorized HTTPS ConexoTech origin")
        if not username or not app_password:
            raise ValueError("WordPress authentication not configured")
        self.origin = parsed.scheme + "://" + parsed.netloc
        self.auth = "Basic " + base64.b64encode((username + ":" + app_password).encode()).decode()

    def call(self, method, route, payload=None):
        endpoint = self.origin + "/wp-json/" + route.lstrip("/")
        raw = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        req = urllib.request.Request(
            endpoint, data=raw, method=method,
            headers={"Authorization": self.auth, "Accept": "application/json",
                     "Content-Type": "application/json", "User-Agent": "ConexoQuality/1"})
        try:
            opener = urllib.request.build_opener(_NoRedirect)
            with opener.open(req, timeout=20) as response:
                actual = urllib.parse.urlparse(response.geturl())
                if actual.scheme != "https" or actual.netloc != urllib.parse.urlparse(self.origin).netloc:
                    raise WPReadError("Unexpected redirect target")
                data = response.read(2_000_000)
        except Exception as exc:
            # Do not log headers, credentials or response containing personal data.
            raise WPReadError("Authenticated WordPress request failed") from exc
        try:
            result = json.loads(data)
        except (ValueError, UnicodeError) as exc:
            raise WPReadError("Invalid WordPress response") from exc
        if not isinstance(result, (dict, list)):
            raise WPReadError("Invalid WordPress response object")
        return result

    def published_pages(self, limit=500):
        """Read-only, paginated catalogue of published posts AND pages.

        Fails closed if either content type exceeds the cap; ASVE must not infer
        that no internal article exists from an incomplete sample.
        """
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("Published content limit invalid")
        output = []
        page_size = min(100, limit)
        max_full_pages = (limit + page_size - 1) // page_size
        for endpoint, prefix in (("posts", "post"), ("pages", "page")):
            page_number = 1
            while page_number <= max_full_pages:
                rows = self.call(
                    "GET",
                    "wp/v2/" + endpoint + "?status=publish&per_page=" +
                    str(page_size) + "&page=" + str(page_number) +
                    "&_fields=id,title,link,status"
                )
                if not isinstance(rows, list):
                    raise WPReadError("Published content endpoint returned invalid data")
                for row in rows:
                    if not isinstance(row, dict) or type(row.get("id")) is not int:
                        continue
                    title = row.get("title")
                    if isinstance(title, dict):
                        title = title.get("rendered", "")
                    output.append({
                        "page_id": prefix + ":" + str(row["id"]),
                        "title": str(title or "")[:240],
                        "url": row.get("link", ""),
                        "status": row.get("status", ""),
                        "content_type": prefix,
                    })
                if len(rows) < page_size:
                    break
                if page_number == max_full_pages:
                    more = self.call(
                        "GET",
                        "wp/v2/" + endpoint + "?status=publish&per_page=1&page=" +
                        str(page_number + 1) + "&_fields=id"
                    )
                    if not isinstance(more, list):
                        raise WPReadError("Published content completeness check failed")
                    if more:
                        raise WPReadError(
                            "Published content catalogue exceeds configured cap; "
                            "increase the safe limit before running ASVE"
                        )
                    break
                page_number += 1
        return output

    def post(self, post_id):
        return self.call("GET", "wp/v2/posts/" + str(post_id) + "?context=edit")

    def media(self, media_id):
        return self.call("GET", "wp/v2/media/" + str(media_id) + "?context=edit")

    def gate_snapshot(self, post_id):
        return self.call("GET", "conexo/v1/editorial/snapshot/" + str(post_id))

    def submit_quality(self, post_id, report, snapshot_sha):
        return self.call("POST", "conexo/v1/editorial/quality/record", {
            "post_id": post_id, "report": report, "snapshot_sha256": snapshot_sha,
        })


def _private_db(db_path):
    raw = Path(db_path).expanduser()
    # Do not resolve the target before testing: resolve() follows symlinks.
    if raw.is_symlink():
        raise ValueError("Symlink DB forbidden")
    path = raw.absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Symlink DB forbidden")
    conn = sqlite3.connect(str(path))
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        conn.close()
        raise
    conn.execute("""CREATE TABLE IF NOT EXISTS quality_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wp_post_id INTEGER NOT NULL,
        fingerprint TEXT NOT NULL,
        status TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        report_json TEXT NOT NULL
    )""")
    conn.commit()
    return conn


def _gate_snapshot_sha(post):
    """Map raw REST fields to the audited RC5 snapshot; never reuse review hash."""
    required = ("id", "type", "status", "date_gmt", "author", "title",
                "content", "excerpt", "slug", "categories", "featured_media")
    if any(key not in post for key in required):
        raise WPReadError("Raw fields required to bind Gate snapshot")
    if (type(post["id"]) is not int or type(post["author"]) is not int
            or post["author"] <= 0 or type(post["featured_media"]) is not int
            or not isinstance(post["categories"], list)
            or not all(type(cat) is int for cat in post["categories"])
            or post["status"] != "draft"):
        raise WPReadError("Invalid draft fields for Gate snapshot")
    raw = {}
    for field in ("title", "content", "excerpt"):
        value = post[field]
        if not isinstance(value, dict) or not isinstance(value.get("raw"), str):
            raise WPReadError("Gate binding requires raw editorial fields")
        raw[field] = value["raw"]
    if not all(isinstance(post[key], str) for key in ("type", "date_gmt", "slug")):
        raise WPReadError("Invalid Gate snapshot metadata")
    snapshot = {
        "ID": post["id"], "post_type": post["type"],
        "post_status": post["status"], "post_date_gmt": post["date_gmt"].replace("T", " "),
        "post_author": post["author"], "post_title": raw["title"],
        "post_content": raw["content"], "post_excerpt": raw["excerpt"],
        "post_name": post["slug"], "post_category": sorted(post["categories"]),
        "meta_input": {"_thumbnail_id": post["featured_media"]},
    }
    return snapshot, _canonical_sha(snapshot)


def _canonical_sha(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def review_once(client, post_id, evidence, db_path, *, submit_quality=False,
                run_asve=False, asve_analyzer=None, topic_db_path=None,
                register_asve_topics=False, asve_receipt=None, asve_decisions=None):
    if type(post_id) is not int or post_id <= 0:
        raise ValueError("post_id invalid")
    if register_asve_topics and not run_asve:
        raise ValueError("ASVE topic registration requires run_asve=True")
    first = client.post(post_id)
    if not isinstance(first, dict) or first.get("status") != "draft" or first.get("id") != post_id:
        raise WPReadError("WordPress post is not the requested draft")
    media_id = first.get("featured_media")
    media = client.media(media_id) if type(media_id) is int and media_id > 0 else None
    report = avaliar_artigo(
        first, media=media,
        fontes=evidence.get("fontes", []),
        evidencias=evidence.get("evidencias", {}),
        corpo_original_fonte=evidence.get("corpo_original_fonte"),
    )
    asve_result = None
    gate_traceability_sidecar = None
    primary_review_for_trace = deepcopy(report)
    if run_asve:
        dossier = evidence.get("asve_dossier")
        if not isinstance(dossier, dict):
            raise ValueError("ASVE requires a complete asve_dossier in the evidence file")
        raw_content = first.get("content")
        if not isinstance(raw_content, dict) or not isinstance(raw_content.get("raw"), str):
            raise WPReadError("ASVE requires raw article content for exact version binding")
        from mkt_flow_p0.revisor_qualidade_unico import executar_revisao_com_asve
        pages = client.published_pages(limit=500)
        asve_result = executar_revisao_com_asve(
            report, raw_content["raw"], dossier, pages, analyzer=asve_analyzer,
            decisoes=asve_decisions, recibo_existente=asve_receipt
        )
        report = asve_result["review"]
        report["asve_receipt"] = asve_result["secondary_analysis"]
        from mkt_flow_p0.editorial_gate_traceability import build_gate_traceability_sidecar
        gate_traceability_sidecar = build_gate_traceability_sidecar(
            raw_content["raw"], dossier, primary_review_for_trace,
            asve_result["secondary_analysis"], pages, asve_decisions
        )
    # Detect concurrent edits between read and commit of the private report.
    latest = client.post(post_id)
    if not isinstance(latest, dict) or latest.get("status") != "draft" or not verificar_versao(report, latest):
        raise WPReadError("Article changed while reviewing; rerun")
    # Persist receipts and optional sidecar only after the exact WordPress version
    # has been re-read and matched. The sidecar is NOT accepted by Gate v1.
    if gate_traceability_sidecar is not None:
        report["gate_traceability_sidecar"] = gate_traceability_sidecar
    # Persist P2 only after the exact WordPress version has been re-read and matched.
    if run_asve and asve_result and register_asve_topics:
        report["asve_future_topics_registered"] = []
        from mkt_flow_p0.fila_pautas import registrar_topico_asve
        for finding in asve_result["secondary_analysis"].get("findings", []):
            if finding.get("priority") == "P2":
                saved_topic = registrar_topico_asve(
                    finding["future_topic"],
                    origin_article_id="wp:" + str(post_id),
                    origin_article_sha256=asve_result["secondary_analysis"]["article_sha256"],
                    finding_id=finding["finding_id"],
                    db_path=topic_db_path,
                )
                report["asve_future_topics_registered"].append(saved_topic)
    with _private_db(db_path) as conn:
        conn.execute("""INSERT INTO quality_reviews
          (wp_post_id, fingerprint, status, checked_at, report_json)
          VALUES (?, ?, ?, ?, ?)""",
          (post_id, report["fingerprint"], report["veredito"],
           datetime.now(timezone.utc).isoformat(),
           json.dumps(report, ensure_ascii=False, sort_keys=True)))
    response = None
    if submit_quality:
        if report["veredito"] != "APTO_PARA_APROVACAO":
            raise WPReadError("Quality review not ready; no remote write performed")
        # The Gate snapshot hash uses a different canonical schema from the
        # read-only Python review hash. Both must be checked independently.
        snapshot = client.gate_snapshot(post_id)
        snapshot_sha = snapshot.get("snapshot_sha256")
        if not isinstance(snapshot_sha, str) or not re.fullmatch(r"[a-f0-9]{64}", snapshot_sha):
            raise WPReadError("Gate snapshot unavailable; no remote write")
        expected_snapshot, expected_sha = _gate_snapshot_sha(latest)
        if snapshot.get("snapshot") != expected_snapshot or snapshot_sha != expected_sha:
            raise WPReadError("Gate snapshot does not match reviewed draft")
        again = client.post(post_id)
        if (not isinstance(again, dict) or again.get("status") != "draft"
                or not verificar_versao(report, again)
                or _gate_snapshot_sha(again)[1] != expected_sha):
            raise WPReadError("Version changed before quality submit")
        response = client.submit_quality(post_id, report, snapshot_sha)
        if (not isinstance(response, dict) or response.get("recorded") is not True
                or type(response.get("post_id")) is not int or response["post_id"] != post_id
                or response.get("snapshot_sha256") != snapshot_sha):
            raise WPReadError("Gate did not acknowledge quality record")
    return report, response


def main(argv=None):
    parser = argparse.ArgumentParser(description="Conexo read-only article review")
    parser.add_argument("--post-id", type=int, required=True)
    parser.add_argument("--evidence-file", required=True)
    parser.add_argument("--db", default=os.environ.get("CONEXO_QUALITY_DB", "/tmp/conexo-private-quality.sqlite"))
    parser.add_argument("--secondary-analysis", action="store_true",
                        help="Run an independent ASVE pass using the existing provider budget")
    parser.add_argument("--register-asve-topics", action="store_true",
                        help="Explicitly persist P2 findings to the shared existing editorial queue")
    parser.add_argument("--asve-receipt-file",
                        help="Reuse a previous receipt for the exact article version; avoids another model call")
    parser.add_argument("--asve-decisions-file",
                        help="JSON list of owner decisions bound to the receipt article_sha256")
    parser.add_argument("--asve-receipt-output-file",
                        help="Write the new ASVE receipt to a new private JSON file (never overwrites)")
    parser.add_argument("--gate-traceability-output-file",
                        help="Export a hash-linked Gate sidecar; current cxeg-package:v1 does not consume it")
    parser.add_argument("--submit-quality", action="store_true",
                        help="Requires independent human-reviewer WordPress identity; does NOT publish")
    args = parser.parse_args(argv)
    site = os.environ.get("CONEXO_WP_URL", "")
    user = os.environ.get("CONEXO_WP_USER", "")
    password = os.environ.get("CONEXO_WP_APP_PASSWORD", "")
    file_path = Path(args.evidence_file)
    if not file_path.is_file():
        parser.error("Evidence file not found")
    evidence = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        parser.error("Evidence must be JSON object")
    if (args.register_asve_topics and not args.secondary_analysis):
        parser.error("--register-asve-topics requires --secondary-analysis")
    if (args.gate_traceability_output_file and not args.secondary_analysis):
        parser.error("--gate-traceability-output-file requires --secondary-analysis")
    if (args.asve_receipt_file or args.asve_decisions_file or args.asve_receipt_output_file) and not args.secondary_analysis:
        parser.error("ASVE receipt/decision files require --secondary-analysis")
    if args.asve_decisions_file and not args.asve_receipt_file:
        parser.error("--asve-decisions-file requires --asve-receipt-file")
    cached_receipt = None
    decisions = None
    if args.asve_receipt_file:
        receipt_path = Path(args.asve_receipt_file)
        if not receipt_path.is_file() or receipt_path.stat().st_size > 200000:
            parser.error("ASVE receipt file missing or too large")
        cached_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if args.asve_decisions_file:
        decisions_path = Path(args.asve_decisions_file)
        if not decisions_path.is_file() or decisions_path.stat().st_size > 50000:
            parser.error("ASVE decisions file missing or too large")
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            parser.error("ASVE decisions must be a JSON list")
    client = WPClient(site, user, password)
    report, response = review_once(
        client, args.post_id, evidence, args.db,
        submit_quality=args.submit_quality, run_asve=args.secondary_analysis,
        register_asve_topics=args.register_asve_topics,
        asve_receipt=cached_receipt, asve_decisions=decisions
    )
    if args.asve_receipt_output_file:
        if not args.secondary_analysis or "asve_receipt" not in report:
            parser.error("No ASVE receipt available to export")
        output_path = Path(args.asve_receipt_output_file).expanduser()
        if output_path.exists() or output_path.is_symlink():
            parser.error("ASVE receipt output exists; refusing overwrite")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(output_path), flags, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report["asve_receipt"], handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
    if args.gate_traceability_output_file:
        sidecar = report.get("gate_traceability_sidecar")
        if not isinstance(sidecar, dict):
            parser.error("No Gate traceability sidecar available")
        output_path = Path(args.gate_traceability_output_file).expanduser()
        if output_path.exists() or output_path.is_symlink():
            parser.error("Gate traceability output exists; refusing overwrite")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(output_path), flags, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(sidecar, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\\n")
    # Only status/fingerprint/check names; no confidential evidence or secrets in logs.
    print(json.dumps({
        "post_id": report["post_id"],
        "fingerprint": report["fingerprint"],
        "veredito": report["veredito"],
        "bloqueios": report["bloqueios"], "pendencias": report["pendencias"],
        "stored_private": True,
        "sent_to_gate": response is not None,
        "asve_status": report.get("secondary_analysis_status", "NOT_RUN"),
        "asve_findings": report.get("secondary_analysis", {}).get("finding_count", 0),
        "asve_future_topics_registered": len(report.get("asve_future_topics_registered", [])),
        "asve_topic_persistence_enabled": args.register_asve_topics,
        "gate_traceability_status": report.get("gate_traceability_sidecar", {}).get("handoff_status", "NOT_CREATED"),
        "gate_sidecar_exported": bool(args.gate_traceability_output_file),
        "gate_current_contract_consumes_sidecar": False,
    }, ensure_ascii=False))
    return 0 if report["veredito"] == "APTO_PARA_APROVACAO" else 2


if __name__ == "__main__":
    sys.exit(main())
