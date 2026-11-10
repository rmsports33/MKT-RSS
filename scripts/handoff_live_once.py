"""One authorized live handoff; public receipt and encrypted private evidence.

Only the isolated homolog branch uses this helper. It does not publish articles,
change the main branch, export credentials, or schedule subsequent generation.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def seal_directory(root, public_key, destination):
    """AES-GCM authenticated payload; RSA-OAEP-SHA256 wraps its random key."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root))
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, buffer.getvalue(), b"mkt-handoff-live/1")
    public = serialization.load_pem_public_key(public_key)
    wrapped = public.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                                             algorithm=hashes.SHA256(), label=None))
    result = {"schema":"mkt-handoff-live/1", "nonce":base64.b64encode(nonce).decode(),
              "wrapped_key":base64.b64encode(wrapped).decode(),
              "ciphertext":base64.b64encode(ciphertext).decode(),
              "ciphertext_sha256":hashlib.sha256(ciphertext).hexdigest()}
    destination.write_text(json.dumps(result), encoding="utf-8")


def main():
    root = Path("work/handoff-live/private")
    root.mkdir(parents=True, mode=0o700)
    report_dir = Path("work/handoff-live/public")
    report_dir.mkdir(mode=0o700)
    report = {"schema":"mkt-live-handoff-receipt/1", "mode":"handoff",
              "free_quota":"CONFIRMED_BY_OWNER_IN_CURRENT_SESSION",
              "wordpress_written":False,"publication_authorized":False,
              "quality_approved":False, "human_acceptance":"PENDING"}
    code = 2
    try:
        if os.environ.get("QUOTA_CONFIRMATION") != "QUOTA_GRATUITA":
            raise ValueError("quota_confirmation_missing")
        if any(os.environ.get(k) for k in ("WP_URL","WP_USER","WP_APP_PASSWORD","TURSO_AUTH_TOKEN")):
            raise ValueError("unexpected_write_credential")
        command = [sys.executable,"pipeline_rss.py","--fonte","tecnoblog","--limit","1",
                   "--handoff-only","--handoff-dir",str(root/"handoffs")]
        output = subprocess.run(command, capture_output=True, timeout=390)
        for name, value in (("stdout.jsonl",output.stdout),("stderr.log",output.stderr)):
            secret=os.environ.get("GROQ_API_KEY","").encode()
            if secret:value=value.replace(secret,b"[REDACTED]")
            (root/name).write_bytes(value)
        report["process_exit_code"]=output.returncode
        events=[]
        for line in output.stdout.decode("utf-8",errors="replace").splitlines():
            try:events.append(json.loads(line))
            except ValueError:continue
        results=[x for x in events if x.get("acao")=="pacote_editorial_criado"]
        report["expected_results"]=len(results)
        report["actions"]=[x.get("acao") for x in events if "acao" in x]
        if output.returncode or len(results)!=1:
            raise ValueError("no_single_expected_handoff")
        item=results[0]
        if item.get("escreveu") is not False:
            raise ValueError("unexpected_write_result")
        from mkt_flow_p0.editorial_identity import validar_handoff_chatgpt
        packet=json.loads(Path(item["handoff_path"]).read_text())
        check=validar_handoff_chatgpt(packet)
        metadata=packet["metadata"]
        review=metadata.get("editorial_substance_review") or {}
        report.update({"outcome":"HANDOFF_CREATED", "version_sha256":check["version_sha256"],
            "content_sha256":hashlib.sha256(packet["markdown"].encode()).hexdigest(),
            "sources_count":check["source_count"], "claims_pending":check["claims_pending"],
            "quality_status":item.get("quality_status"),"quality_pending":item.get("quality_pending",[]),
            "quality_words":item.get("quality_words"),
            "brief_present":isinstance(metadata.get("editorial_brief"),dict),
            "voice_application":metadata.get("editorial_voice_application",{}).get("status"),
            "substantive_scores":{k:v.get("score") for k,v in review.get("criteria",{}).items()},
            "review_method":review.get("method"),
            "review_diagnostics":item.get("review_diagnostics",[]),
            "review_attempt_count":item.get("review_attempt_count")})
        code=0
    except Exception as exc:
        report.update(outcome="BLOCKED", error_type=type(exc).__name__)
    finally:
        (report_dir/"manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        seal_directory(root,Path("data/homolog/handoff-live-public.pem").read_bytes(),
                       report_dir/"handoff-encrypted.json")
        print(json.dumps(report))
        if os.getenv("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as out:
                out.write("```json\n"+json.dumps(report,indent=2)+"\n```\n")
    return code


if __name__=="__main__":
    raise SystemExit(main())
