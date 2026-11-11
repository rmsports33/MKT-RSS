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
        if not isinstance(result, dict):
            raise WPReadError("Invalid WordPress object")
        return result

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


def review_once(client, post_id, evidence, db_path, *, submit_quality=False):
    if type(post_id) is not int or post_id <= 0:
        raise ValueError("post_id invalid")
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
    # Detect concurrent edits between read and commit of the private report.
    latest = client.post(post_id)
    if not isinstance(latest, dict) or latest.get("status") != "draft" or not verificar_versao(report, latest):
        raise WPReadError("Article changed while reviewing; rerun")
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
    client = WPClient(site, user, password)
    report, response = review_once(client, args.post_id, evidence, args.db,
                                   submit_quality=args.submit_quality)
    # Only status/fingerprint/check names; no confidential evidence or secrets in logs.
    print(json.dumps({
        "post_id": report["post_id"],
        "fingerprint": report["fingerprint"],
        "veredito": report["veredito"],
        "bloqueios": report["bloqueios"], "pendencias": report["pendencias"],
        "stored_private": True,
        "sent_to_gate": response is not None,
    }, ensure_ascii=False))
    return 0 if report["veredito"] == "APTO_PARA_APROVACAO" else 2


if __name__ == "__main__":
    sys.exit(main())
