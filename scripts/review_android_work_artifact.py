"""Re-run genuine PR #24 review against prior GitHub Actions source artifact."""
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

from mkt_flow_p0.chatgpt_work_handoff import preparar_pacote_completo, avaliar_retorno

ARTIFACT = 12667627880
CLAIMS = [
    ("c1-findhub", "Soon, you’ll be able to ask Gemini to remember where you placed important items"),
    ("c2-motion", "Motion Assist, which adds a subtle bubble overlay to your screen"),
    ("c3-guided", "Guided vision is coming soon to phones running Android 9+"),
    ("c4-keep", "Rollout starts today in Google Messages."),
    ("c5-theme", "With Chat theme in Google Messages, you can customize each chat"),
]

def main():
    token = os.environ["GITHUB_TOKEN"]
    req = Request("https://api.github.com/repos/rmsports33/MKT-RSS/actions/artifacts/"
                  + str(ARTIFACT) + "/zip",
                  headers={"Authorization": "Bearer " + token,
                           "Accept": "application/vnd.github+json",
                           "User-Agent": "conexo-pr24-review"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read(1_000_000)
    with ZipFile(io.BytesIO(raw)) as arc:
        original = json.loads(arc.read("android_drop_package.json"))
    payload = original["payload"]
    contract = payload["contrato"]
    captures = payload["capturas"]
    capture = captures["google-android-drop-sep2026"]
    assert capture["sha256_texto"] == "129b2ec292812751745958b8f1f3ddd4c1f512b31aa5a24fcf402791da011f68"
    body = capture["texto"]
    for claim_id, quote in CLAIMS:
        if " ".join(quote.split()).casefold() not in " ".join(body.split()).casefold():
            raise ValueError("Claim absent from original snapshot: " + claim_id)
    contract["claims"] = [
        {"id": cid, "status": "PASS", "text": quote,
         "evidence_ids": ["google-android-drop-sep2026"]}
        for cid, quote in CLAIMS]
    package = preparar_pacote_completo(contract, captures)
    response = json.loads(Path("tests/fixtures/android_work_response_supervised.json").read_text(encoding="utf-8"))
    report = avaliar_retorno(package, response)
    assert report["acao"] == "bloqueado" and report["escreveu"] is False
    assert report["verificacao_factual"] == "NAO_VERIFICADO"
    assert report["auditoria_cobertura"]["veredito"] == "REVISAO_SEMANTICA_PENDENTE", report
    assert len(report["auditoria_cobertura"]["candidatas_traducao"]) == 5, report
    assert report["revisao_humana_pendente"] is True
    out = Path("evidence-review-output")
    out.mkdir(exist_ok=True)
    (out / "package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps({
        "original_artifact_id": ARTIFACT, "original_capture_sha256": capture["sha256_texto"],
        "package_sha256": package["sha256"], "claim_count": len(CLAIMS),
        "verdict": report["auditoria_cobertura"]["veredito"], "wordpress_written": False
    }, indent=2), encoding="utf-8")
    print("REVIEW_OK claims", len(CLAIMS), "mapped",
          len(report["auditoria_cobertura"]["candidatas_traducao"]),
          "verdict", report["auditoria_cobertura"]["veredito"],
          "package_sha256", package["sha256"])

if __name__ == "__main__":
    main()
