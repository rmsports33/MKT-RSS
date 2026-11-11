"""Read only the WordPress identity of the existing MKT-RSS credential.

No writes, redirects, retries, article reads or secret-bearing diagnostics.
Run inside the executor holding WP_URL, WP_USER and WP_APP_PASSWORD.
"""
import base64
import json
import os
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

SITE = "https://conexotech.com.br"
EXPECTED_ID = 4
MAX_BODY = 65536


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_identity(environ, *, opener=None):
    url = environ.get("WP_URL", "")
    user = environ.get("WP_USER", "")
    password = environ.get("WP_APP_PASSWORD", "")
    if not isinstance(url, str) or url.rstrip("/") != SITE:
        return "WP_ORIGIN_NOT_ALLOWED"
    if not isinstance(user, str) or not user.strip() or not isinstance(password, str) or not password.strip():
        return "WP_CREDENTIAL_MISSING"
    auth = base64.b64encode((user + ":" + password).encode("utf-8")).decode("ascii")
    request = Request(
        SITE + "/wp-json/wp/v2/users/me?context=edit&_fields=id,roles,capabilities",
        headers={"Authorization": "Basic " + auth, "Accept": "application/json",
                 "User-Agent": "MKT-RSS-Identity-Preflight/1"}, method="GET")
    client = opener if opener is not None else build_opener(NoRedirect())
    try:
        with client.open(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != request.full_url:
                return "WP_READ_NOT_CONFIRMED"
            raw = response.read(MAX_BODY + 1)
            if len(raw) > MAX_BODY:
                return "WP_RESPONSE_TOO_LARGE"
            identity = json.loads(raw)
    except HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            return "WP_REDIRECT_BLOCKED"
        return "WP_AUTH_REJECTED" if exc.code in (401, 403) else "WP_HTTP_REJECTED"
    except (URLError, OSError, ValueError, HTTPException):
        return "WP_READ_FAILED"
    if not isinstance(identity, dict):
        return "WP_IDENTITY_INVALID"
    if type(identity.get("id")) is not int or identity["id"] != EXPECTED_ID:
        return "WP_IDENTITY_MISMATCH"
    roles = identity.get("roles")
    caps = identity.get("capabilities")
    if (not isinstance(roles, list) or "editor" not in roles or "administrator" in roles
            or not isinstance(caps, dict)
            or ("manage_options" in caps and caps["manage_options"] is not False)):
        return "WP_PRIVILEGE_DENIED"
    if any(caps.get(name) is not True for name in ("read", "edit_posts", "publish_posts")):
        return "WP_PERMISSION_MISSING"
    return "PASS"


def main():
    code = check_identity(os.environ)
    if code == "PASS":
        result = "PASS: MKT-RSS WordPress credential authenticated as editor ID 4; no writes or publication."
    else:
        result = "BLOCKED: " + code
    print(result)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write(result + "\n")
    return 0 if code == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
