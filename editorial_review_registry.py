"""Ed25519 authenticated registry boundary for the independent review.

Fase B (offline, 19/11/2026). This module implements only the protocol and the
authenticated registry boundary of contract `BROKER_REVISOR_GATE_CONTRACT_20261119`
v2.3. It does NOT publish, does not write WordPress and is not the broker.

The registry envelope is signed as a whole (protocol_version, alg, kid, record,
served_at and registry_seq). The lookup callback is transport only. A replayed
or stale envelope is rejected even when its signature is valid.
"""
import json
import threading

_ALG = "Ed25519"
_PROTOCOL = 1
_SIG_HEX_LEN = 128


def canonical_bytes(value):
    """Canonical UTF-8 JSON shared by the issuer and every verifier."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _signature_ok(verification_key, message, signature):
    if not isinstance(signature, str) or len(signature) != _SIG_HEX_LEN:
        return False
    if not hasattr(verification_key, "verify"):
        return False
    try:
        verification_key.verify(bytes.fromhex(signature), message)
        return True
    except Exception:
        # InvalidSignature, malformed keys/signatures and bad encodings fail closed.
        return False


class InMemorySequenceStore:
    """Persistent-store stand-in for OFFLINE tests, with CAS semantics.

    Production Fase C must replace it with the MySQL/MariaDB InnoDB table and
    error-1062 handling described in section 6.4 of the contract. No client
    memory is a security requirement: this store models the SERVER's decision.
    """

    def __init__(self, rows=None):
        self._rows = dict(rows or {})
        self._lock = threading.Lock()

    def accepted(self, record_url, seq):
        """Return True only when seq advances the stored maximum (atomic CAS)."""
        with self._lock:
            current = self._rows.get(record_url, 0)
            if not isinstance(seq, int) or seq <= current:
                return False
            self._rows[record_url] = seq
            return True

    def snapshot(self):
        with self._lock:
            return dict(self._rows)


def sign_registry_envelope(record, *, served_at, registry_seq, private_key, kid,
                           protocol_version=_PROTOCOL):
    """Issuer helper: sign the COMPLETE envelope with an Ed25519 private key."""
    if not isinstance(record, dict) or not hasattr(private_key, "sign"):
        raise ValueError("registry_signing_key_invalid")
    if not isinstance(kid, str) or not kid.strip():
        raise ValueError("registry_kid_missing")
    envelope = {
        "protocol_version": protocol_version, "alg": _ALG, "kid": kid,
        "record": record, "served_at": served_at, "registry_seq": registry_seq,
    }
    envelope["signature"] = private_key.sign(canonical_bytes(envelope)).hex()
    return envelope


def verify_registry_envelope(envelope, verification_key, *, now=None,
                             sequence_store=None, max_age=120, future=30):
    """Verify signature, freshness, TTL, revocation and authoritative sequence."""
    if not isinstance(envelope, dict):
        return {"verified": False, "reason": "review_record_missing"}
    if envelope.get("alg") != _ALG or envelope.get("protocol_version") != _PROTOCOL:
        return {"verified": False, "reason": "review_record_algorithm_unsupported"}
    if not isinstance(envelope.get("kid"), str) or not envelope["kid"].strip():
        return {"verified": False, "reason": "review_record_signature_missing"}
    record = envelope.get("record")
    signature = envelope.get("signature")
    served_at = envelope.get("served_at")
    seq = envelope.get("registry_seq")
    if not isinstance(record, dict) or not isinstance(served_at, int) or not isinstance(seq, int):
        return {"verified": False, "reason": "review_record_evidence_missing"}
    signed = {k: v for k, v in envelope.items() if k != "signature"}
    if not _signature_ok(verification_key, canonical_bytes(signed), signature):
        return {"verified": False, "reason": "review_record_signature_invalid"}

    now = int(now) if isinstance(now, int) else None
    if now is None:
        return {"verified": False, "reason": "review_record_time_unverifiable"}
    if served_at < now - max_age or served_at > now + future:
        return {"verified": False, "reason": "review_record_stale_response"}

    issued = record.get("issued_at")
    expires = record.get("expires_at")
    if (not isinstance(issued, int) or not isinstance(expires, int)
            or issued > now or now >= expires or expires - issued > 3600):
        return {"verified": False, "reason": "review_record_evidence_missing"}
    if (record.get("revoked") is not False or record.get("status") != "FINAL"
            or record.get("independent") is not True
            or not isinstance(record.get("review_record_url"), str)):
        return {"verified": False, "reason": "review_record_mismatch"}

    if sequence_store is None or not hasattr(sequence_store, "accepted"):
        return {"verified": False, "reason": "registry_sequence_store_missing"}
    if not sequence_store.accepted(record["review_record_url"], seq):
        return {"verified": False, "reason": "review_record_replay_detected"}
    return {"verified": True, "reason": None, "record": record}

