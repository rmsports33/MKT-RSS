#!/usr/bin/env python3
"""
Diagnostico da integracao Google Drive
Rode: python diagnostico_drive.py
Mostra exatamente onde travou no Passo 6.1
"""
import os
import sys
from pathlib import Path

print("="*60)
print("DIAGNOSTICO GOOGLE DRIVE - Passo 6.1")
print("="*60)

# 1. Verificar arquivos
print("\n[1] Verificando arquivos...")
files_ok = True
for f in ["google_drive_client.py", "drive_command.py", ".env"]:
    exists = Path(f).exists()
    print(f"  {'[OK]' if exists else '[FALTA]'} {f} -> {Path(f).resolve()}")
    if not exists:
        files_ok = False

# 2. Verificar .env
print("\n[2] Verificando .env...")
from dotenv import load_dotenv
load_dotenv()
client_id = os.getenv('GOOGLE_DRIVE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_DRIVE_CLIENT_SECRET')

if not client_id or client_id == "seu_client_id_aqui":
    print("  [ERRO] GOOGLE_DRIVE_CLIENT_ID nao configurado!")
    print("         Abra o arquivo .env e troque 'seu_client_id_aqui'")
    print("         pelo Client ID real do Google Cloud (passo 1.4)")
else:
    print(f"  [OK] CLIENT_ID = {client_id[:20]}... (tamanho {len(client_id)})")

if not client_secret or client_secret == "seu_client_secret_aqui":
    print("  [ERRO] GOOGLE_DRIVE_CLIENT_SECRET nao configurado!")
else:
    print(f"  [OK] CLIENT_SECRET = {client_secret[:10]}... (tamanho {len(client_secret)})")

# 3. Verificar bibliotecas
print("\n[3] Verificando bibliotecas...")
try:
    import google.auth
    import google_auth_oauthlib
    import googleapiclient
    print("  [OK] google-api-python-client instalado")
    print("  [OK] google-auth-httplib2 instalado")
    print("  [OK] google-auth-oauthlib instalado")
except ImportError as e:
    print(f"  [ERRO] Biblioteca faltando: {e}")
    print("  Rode: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv")

# 4. Verificar token
print("\n[4] Verificando autenticacao...")
if Path("token.json").exists():
    print("  [OK] token.json existe - voce JA autenticou antes")
    print("       Se der erro 401, delete token.json e tente de novo:")
    print("       del token.json  (Windows)  ou  rm token.json (Linux/Mac)")
else:
    print("  [INFO] token.json NAO existe - primeira autenticacao necessaria")
    print("         Ao rodar 'python drive_command.py list', o navegador DEVE abrir")

# 5. Teste real
print("\n[5] Teste de autenticacao (vai tentar abrir o navegador)...")
if client_id and client_id != "seu_client_id_aqui" and client_secret and client_secret != "seu_client_secret_aqui":
    try:
        from google_drive_client import get_client_from_env
        print("  Tentando autenticar... (se travar aqui, veja abaixo)")
        client = get_client_from_env()
        print("  [OK] Autenticacao funcionou!")
        print("  Tentando listar 2 arquivos...")
        files = client.list_files(page_size=2)
        print(f"  [OK] Listagem funcionou! {len(files)} arquivo(s) encontrados")
        for f in files:
            print(f"       - {f['name']}")
    except Exception as e:
        print(f"\n  [ERRO] {e}")
        print("\n  ---- SOLUCOES PARA CADA ERRO ----")
        err = str(e).lower()
        if "invalid_client" in err or "unauthorized" in err:
            print("  -> Client ID/Secret errados. Copie de novo do Google Cloud (Passo 1.4)")
        elif "access blocked" in err or "acesso bloqueado" in err or "not verified" in err:
            print("  -> ERRO MAIS COMUM! Voce esqueceu de adicionar seu email como 'Usuario de teste'")
            print("     Va em Google Cloud > APIs e Servicos > Tela de consentimento OAuth")
            print("     Role ate 'Usuarios de teste' > + ADD USERS > adicione seu gmail")
        elif "redirect_uri_mismatch" in err:
            print("  -> Tipo de credencial errado! Precisa ser 'Aplicativo de desktop'")
            print("     Delete a credencial e crie de novo como Desktop")
        elif "quota" in err:
            print("  -> Cota excedida, aguarde 1 minuto")
        else:
            print("  -> Copie TODO o erro e me envie")
            import traceback
            traceback.print_exc()
else:
    print("  [PULADO] Configure o .env primeiro")

print("\n" + "="*60)
print("FIM DO DIAGNOSTICO")
print("="*60)
print("\nSe o navegador NAO abriu, tente a alternativa manual:")
print("  1. O terminal mostra uma URL comeca com https://accounts.google.com/...")
print("  2. COPIE essa URL e cole no Chrome")
print("  3. Faca login e clique em Permitir")
print("  4. Voce voltara para localhost - pode fechar a aba")
