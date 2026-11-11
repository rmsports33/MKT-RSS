import io
import json
import unittest
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

from tools.wp_identity_preflight import check_identity, SITE, MAX_BODY, NoRedirect

ENV = {"WP_URL": SITE, "WP_USER": "synthetic-editor", "WP_APP_PASSWORD": "synthetic-password"}
IDENTITY = {"id": 4, "roles": ["editor"], "capabilities": {
    "read": True, "edit_posts": True, "publish_posts": True}}


def client(body=IDENTITY, status=200, url=None):
    opener = MagicMock()
    response = opener.open.return_value.__enter__.return_value
    response.status = status
    response.geturl.return_value = url or SITE + "/wp-json/wp/v2/users/me?context=edit&_fields=id,roles,capabilities"
    response.read.return_value = json.dumps(body).encode()
    return opener


class IdentityTests(unittest.TestCase):
    def test_editor_authenticated_by_one_get_only(self):
        opener = client()
        self.assertEqual(check_identity(ENV, opener=opener), "PASS")
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.data)
        self.assertTrue(request.get_header("Authorization").startswith("Basic "))
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)

    def test_credentials_never_sent_to_other_origins(self):
        for url in ("http://conexotech.com.br", SITE + ".evil.example", SITE + "/path", "https://user@conexotech.com.br"):
            opener = client()
            self.assertEqual(check_identity({**ENV, "WP_URL": url}, opener=opener), "WP_ORIGIN_NOT_ALLOWED")
            opener.open.assert_not_called()

    def test_missing_secret_no_network(self):
        opener = client()
        self.assertEqual(check_identity({**ENV, "WP_APP_PASSWORD": ""}, opener=opener), "WP_CREDENTIAL_MISSING")
        opener.open.assert_not_called()

    def test_other_identity_blocked(self):
        for user_id in (3, 5, "4", True):
            self.assertEqual(check_identity(ENV, opener=client({**IDENTITY, "id": user_id})), "WP_IDENTITY_MISMATCH")

    def test_administrator_and_extra_privilege_blocked(self):
        for identity in (
            {**IDENTITY, "roles": ["administrator", "editor"]},
            {**IDENTITY, "capabilities": {**IDENTITY["capabilities"], "manage_options": True}},
        ):
            self.assertEqual(check_identity(ENV, opener=client(identity)), "WP_PRIVILEGE_DENIED")

    def test_missing_publication_permission(self):
        identity = {**IDENTITY, "capabilities": {**IDENTITY["capabilities"], "publish_posts": False}}
        self.assertEqual(check_identity(ENV, opener=client(identity)), "WP_PERMISSION_MISSING")

    def test_auth_rejected_no_response_body_leak(self):
        opener = client()
        opener.open.side_effect = HTTPError(SITE, 401, "sensitive response", {}, io.BytesIO(b"private"))
        self.assertEqual(check_identity(ENV, opener=opener), "WP_AUTH_REJECTED")
        opener.open.assert_called_once()

    def test_redirect_never_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example"))
        opener = client()
        opener.open.side_effect = HTTPError(SITE, 302, "redirect", {}, None)
        self.assertEqual(check_identity(ENV, opener=opener), "WP_REDIRECT_BLOCKED")

    def test_network_failure_no_retry(self):
        opener = client()
        opener.open.side_effect = URLError("sensitive detail")
        self.assertEqual(check_identity(ENV, opener=opener), "WP_READ_FAILED")
        opener.open.assert_called_once()

    def test_malformed_and_oversized_responses(self):
        for body, expected in ((b"invalid", "WP_READ_FAILED"), (b"x" * (MAX_BODY + 1), "WP_RESPONSE_TOO_LARGE")):
            opener = client()
            opener.open.return_value.__enter__.return_value.read.return_value = body
            self.assertEqual(check_identity(ENV, opener=opener), expected)

    def test_success_status_and_origin_must_match(self):
        self.assertEqual(check_identity(ENV, opener=client(status=403)), "WP_READ_NOT_CONFIRMED")
        self.assertEqual(check_identity(ENV, opener=client(url="https://evil.example")), "WP_READ_NOT_CONFIRMED")


if __name__ == "__main__":
    unittest.main()
