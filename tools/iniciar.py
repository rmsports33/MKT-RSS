#!/usr/bin/env python3
"""🚀 INÍCIO RÁPIDO - Este arquivo prepara tudo para você trabalhar.

Não é preciso entender do projeto. Basta rodar este arquivo:
    python tools/iniciar.py

Ele vai:
1. Verificar se tudo está registrado corretamente
2. Atualizar o registro automaticamente (se precisar)
3. Dizer em palavras simples se pode começar ou o que falta
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "REGISTRO_UNICO_20261118.md"


def imprimir(mensagem):
    print(mensagem)


def passo(texto):
    print(f"\n▶ {texto}")


def rodar(comando):
    """Executa um comando e retorna se deu certo ou não."""
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
    )
    return resultado.returncode == 0, (resultado.stdout or "") + (resultado.stderr or "")


def main():
    print("=" * 50)
    print("   🚀 INÍCIO RÁPIDO DO PROJETO MKT-RSS")
    print("=" * 50)

    # Passo 1: Verificar se o registro existe
    if not REGISTRO.exists():
        imprimir("\n❌ ERRO: Não encontrei o arquivo de registro.")
        imprimir("   Esperava: docs/REGISTRO_UNICO_20261118.md")
        imprimir("\n   Peça para alguém recriar este arquivo antes de continuar.")
        return 1

    passo("1/3 Verificando se tudo está registrado...")
    ok, saida = rodar([sys.executable, "tools/check_registro_unico.py"])
    if ok:
        imprimir("   ✅ Tudo registrado corretamente.")
    else:
        imprimir("   ⚠️  Encontrei algo faltando. Vou tentar corrigir sozinho...")
        ok2, saida2 = rodar([sys.executable, "tools/check_registro_unico.py", "--auto"])
        if ok2:
            imprimir("   ✅ Corrigido automaticamente. Agora está tudo certo.")
        else:
            imprimir("   ❌ Não consegui corrigir sozinho. Precisa de ajuda.")
            imprimir(saida2[:500])
            return 1

    passo("2/3 Verificando se pode começar a trabalhar...")
    if ok:
        imprimir("   ✅ Pode começar. Não há pendências.")
    else:
        imprimir("   ⚠️  Ainda há pendências. Revise acima antes de continuar.")
        return 1

    passo("3/3 Resumo do que está pronto...")
    imprimir("   • Registro único: ✅")
    imprimir("   • Verificações: ✅")
    imprimir("   • Pronto para iniciar: ✅")

    imprimir("\n" + "=" * 50)
    print("   ✅ SUCESSO! Você pode começar a trabalhar.")
    print("=" * 50)
    imprimir("\n   Quando terminar, rode novamente este arquivo para salvar tudo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
