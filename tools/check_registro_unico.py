"""Verifica se o registro unico cobre todos os documentos de auditoria.

Falha (exit 1) quando um documento de auditoria existe em docs/ mas nao e
referenciado por docs/REGISTRO_UNICO_20261118.md. Uso antes de cada commit
que inclui auditoria:

    python tools/check_registro_unico.py
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "REGISTRO_UNICO_20261118.md"
PASTA_DOCS = RAIZ / "docs"

PREFIXOS = re.compile(
    r"^(M07_|M11_|M14_|M19_|AUDITORIA_|CREDENCIAL_|GARGALO_|PAUTAS_|"
    r"REGENERACAO_|TRIAGE_|REGISTRO_)"
)


def documentos_de_auditoria():
    for arquivo in sorted(PASTA_DOCS.glob("*.md")):
        if arquivo.name == REGISTRO.name:
            continue
        if PREFIXOS.match(arquivo.name):
            yield arquivo


def faltantes():
    if not REGISTRO.is_file():
        return ["REGISTRO_UNICO_20261118.md ausente"]
    texto = REGISTRO.read_text(encoding="utf-8", errors="replace")
    faltando = []
    for arquivo in documentos_de_auditoria():
        if arquivo.name not in texto and arquivo.stem not in texto:
            faltando.append(arquivo.name)
    return faltando


def main():
    faltando = faltantes()
    if not faltando:
        print("OK: registro unico cobre todos os documentos de auditoria")
        return 0
    print("PENDENTE: documentos de auditoria fora do registro unico:")
    for nome in faltando:
        print(f"  - {nome}")
    print("\nAdicione uma referencia em docs/REGISTRO_UNICO_20261118.md e rode de novo.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
