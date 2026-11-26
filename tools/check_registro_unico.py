"""Verifica se o registro unico cobre todos os documentos de auditoria.

    python tools/check_registro_unico.py             # falha se faltar referencia
    python tools/check_registro_unico.py --auto      # atualiza a secao automatica
"""
import argparse
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "REGISTRO_UNICO_20261118.md"
PASTA_DOCS = RAIZ / "docs"
AUTO_INICIO = "<!-- registro-unico:auto:start -->"
AUTO_FIM = "<!-- registro-unico:auto:end -->"

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


def titulo_de(arquivo):
    try:
        for linha in arquivo.read_text(encoding="utf-8",
                                       errors="replace").splitlines():
            if linha.startswith("#"):
                return linha.lstrip("# ").strip()[:100] or arquivo.stem
    except OSError:
        return arquivo.stem
    return arquivo.stem


def conteudo_auto():
    linhas = [AUTO_INICIO,
              "",
              "## Documentos de auditoria reconhecidos (atualizado automaticamente)",
              ""]
    for arquivo in documentos_de_auditoria():
        linhas.append(f"- `docs/{arquivo.name}` — {titulo_de(arquivo)}")
    linhas.append("")
    linhas.append(AUTO_FIM)
    return "\n".join(linhas)


def atualizar_registro():
    texto = REGISTRO.read_text(encoding="utf-8", errors="replace") if REGISTRO.exists() else ""
    bloco = conteudo_auto()
    if AUTO_INICIO in texto and AUTO_FIM in texto:
        antes = texto[:texto.index(AUTO_INICIO)]
        depois = texto[texto.index(AUTO_FIM) + len(AUTO_FIM):]
        texto = antes.rstrip() + "\n\n" + bloco + "\n" + depois.lstrip()
    else:
        texto = texto.rstrip() + "\n\n" + bloco + "\n"
    REGISTRO.write_text(texto, encoding="utf-8")
    return 0


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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    if args.auto:
        atualizar_registro()
        print("REGISTRO_UNICO_20261118.md atualizado (secao automatica)")
        return 0

    faltando = faltantes()
    if not faltando:
        print("OK: registro unico cobre todos os documentos de auditoria")
        return 0
    print("PENDENTE: documentos de auditoria fora do registro unico:")
    for nome in faltando:
        print(f"  - {nome}")
    print("\nExecute: python tools/check_registro_unico.py --auto")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
