import hashlib
import hmac
import json
from editorial_atomic_transition import supervised_atomic_publish
from editorial_factual_certificate import draft_digest

KEY = b"independent-review-backend-key-32bytes-12345"
POST = {"id": 41, "title": "Notícia", "content": "<p>Texto</p>",
        "slug": "noticia", "categories": [10], "featured_media": 12, "status": "draft"}
OP = "operation-id-unique-0001"

def cert(post=POST):
    data = {"draft_sha256": draft_digest(post), "reviewer_id": "human-reviewer",
            "evidence_refs": ["https://example.org/source"], "decision": "APROVADO",
            "issued_at": 100, "expires_at": 200}
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode()
    return {**data, "signature": hmac.new(KEY, encoded, hashlib.sha256).hexdigest()}

def test_no_backend_never_publishes():
    assert not supervised_atomic_publish(POST, cert(), KEY, OP, None, now=150)["published"]

def test_certificate_must_be_valid_before_backend_call():
    called = []
    result = supervised_atomic_publish({**POST, "content": "changed"}, cert(), KEY, OP,
                                       lambda *args: called.append(args), now=150)
    assert not result["published"]
    assert not called

def test_backend_failure_never_reports_success():
    def fail(*_):
        raise ConnectionError("unavailable")
    result = supervised_atomic_publish(POST, cert(), KEY, OP, fail, now=150)
    assert not result["published"]

def test_backend_commit_requires_confirmed_post_and_status():
    for response in (None, {}, {"committed": False, "post_id": 41, "status": "publish"},
                     {"committed": True, "post_id": 42, "status": "publish"},
                     {"committed": True, "post_id": 41, "status": "draft"}):
        result = supervised_atomic_publish(POST, cert(), KEY, OP, lambda *_: response, now=150)
        assert not result["published"]

def test_atomic_backend_can_prevent_duplicate_operation():
    committed = set()
    def atomic(post_id, digest, operation_id, certificate):
        if operation_id in committed:
            return {"committed": False, "post_id": post_id, "status": "publish"}
        committed.add(operation_id)
        return {"committed": True, "post_id": post_id, "status": "publish"}
    assert supervised_atomic_publish(POST, cert(), KEY, OP, atomic, now=150)["published"]
    assert not supervised_atomic_publish(POST, cert(), KEY, OP, atomic, now=150)["published"]

def test_invalid_operation_id_blocks_before_backend():
    called = []
    result = supervised_atomic_publish(POST, cert(), KEY, "short",
                                       lambda *args: called.append(args), now=150)
    assert not result["published"]
    assert not called
