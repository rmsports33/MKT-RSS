"""Capture official source body into a transient CI artifact, no publishing."""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from mkt_flow_p0.captura_completa import criar_captura_completa, verificar_captura_completa

URL = "https://blog.google/products-and-platforms/platforms/android/android-drop-september-2026/"
TITLE = "September Android Drop: Remember where you put things, ease motion sickness, and more"


def main():
    from trafilatura import extract
    request = Request(URL, headers={"User-Agent": "ConexoOS-EvidenceCapture/1.0"})
    with urlopen(request, timeout=25) as response:
        actual_url = response.geturl()
        if actual_url != URL:
            raise ValueError("Unapproved HTTP redirect")
        html = response.read(2_000_001)
        if len(html) > 2_000_000:
            raise ValueError("HTML beyond bounded maximum")
    text = extract(html.decode("utf-8", errors="replace"), include_comments=False)
    if not text or len(text.split()) < 100:
        raise ValueError("Primary-source extraction failed or incomplete")
    if "Rollout starts today in Google Messages." not in text:
        raise ValueError("Previously reviewed claim absent from captured source")
    capture = criar_captura_completa(URL, text, titulo=TITLE)
    if not verificar_captura_completa(capture):
        raise ValueError("Snapshot integrity failure")
    contract = {
        "contract_version": "1.0", "content_type": "noticia", "status": "PASS",
        "sources": [{"id": "google-android-drop-sep2026", "status": "PASS",
                     "url": URL, "retrieved_at": capture["capturado_em"]}],
        "claims": [{"id": "google-keep-rollout", "status": "PASS",
                    "text": "Rollout starts today in Google Messages.",
                    "evidence_ids": ["google-android-drop-sep2026"]}],
    }
    from mkt_flow_p0.chatgpt_work_handoff import preparar_pacote_completo
    package = preparar_pacote_completo(contract, {"google-android-drop-sep2026": capture})
    path = Path("evidence-output")
    path.mkdir(exist_ok=True)
    (path / "android_drop_package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2))
    (path / "capture_manifest.json").write_text(json.dumps({
        "url": URL, "timestamp": capture["capturado_em"],
        "word_count": capture["palavras"],
        "sha256_texto": capture["sha256_texto"],
        "sha256_payload": package["sha256"],
        "claim_count": len(contract["claims"]),
        "factual_certification": False,
        "publication_allowed": False,
    }, indent=2))
    print("CAPTURE_OK", "words", capture["palavras"], "sha256", capture["sha256_texto"])
    print("PACKAGE_OK", "claims", len(contract["claims"]), "sha256", package["sha256"])


if __name__ == "__main__":
    main()
