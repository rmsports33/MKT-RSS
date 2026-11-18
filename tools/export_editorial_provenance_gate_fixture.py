"""Export a deterministic marker fixture using the real MKT-RSS producer.

The output is intended for an isolated cross-language Gate contract test only.
It contains no production post, credentials, network calls or WordPress writes.
"""
import argparse
from pathlib import Path

from mkt_flow_p0.editorial_provenance import MODULOS_OBRIGATORIOS, marcar


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    body = (
        "<h2>Fixture de contrato RC10.5</h2>\n"
        "<p>Conteudo sintetico gerado pelo produtor MKT-RSS para validar "
        "a compatibilidade do fingerprint com o Gate PHP.</p>"
    )
    marked, manifest = marcar(
        body,
        modules={name: "EXECUTED" for name in MODULOS_OBRIGATORIOS},
        voice_status="ASSISTED_ADAPTED",
        substance_status="PASS",
        image_rights_confirmed=True,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(marked, encoding="utf-8")
    print({
        "output": str(args.output),
        "version_sha256": manifest["version_sha256"],
        "content_sha256": manifest["content_sha256"],
        "bytes": len(marked.encode("utf-8")),
    })


if __name__ == "__main__":
    main()
