"""
mkt_flow_p0.config — Validação fail-fast de .env para P0.
Nunca imprime segredos em log. Lista clara do que falta.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cofre único fora dos repos (nuvem/multi) — fonte primária
CENTRAL = Path.home() / ".conexotech.env"
if CENTRAL.exists():
    load_dotenv(CENTRAL, override=False)
# Carrega .env da raiz do projeto e de MKTFLOW (compatibilidade, fallback)
ROOT = Path(__file__).parent.parent
for p in [ROOT / ".env", ROOT / "MKTFLOW" / ".env", Path.cwd() / ".env"]:
    if p.exists():
        load_dotenv(p, override=False)

# Definição de variáveis por perfil
REQUIRED_P0 = {
    # Para pipeline ML->WP, WP é obrigatório; Groq é obrigatório para geração
    "GROQ_API_KEY": "Obrigatório para geração de conteúdo (obtenha em https://console.groq.com)",
    "WP_URL": "URL do WordPress (ex: https://seusite.com) — necessário para publicação",
    "WP_USER": "Usuário WordPress com Application Password",
    "WP_APP_PASSWORD": "Application Password do WordPress (Perfil > Application Passwords)",
}

OPTIONAL_P0 = {
    "GROQ_MODEL": "Modelo Groq (default: openai/gpt-oss-120b)",
    "GOOGLE_DRIVE_CLIENT_ID": "Para upload Drive (opcional em P0)",
    "GOOGLE_SHEETS_ID": "Para pipeline comparativo (opcional em P0)",
    "GA_MEASUREMENT_ID": "Google Analytics 4 (ex: G-XXXXXXXXXX) — injetado nas landings p/ medir cliques",
}

def validate_env(strict: bool = False, required_keys=None) -> dict:
    """
    Valida .env. Se strict=True ou required_keys fornecido, falha se faltar.
    Retorna dict com valores (sem expor segredos no log).
    """
    required = required_keys if required_keys is not None else REQUIRED_P0
    missing = []
    present = {}
    for k, desc in required.items():
        v = os.getenv(k, "").strip()
        if not v:
            missing.append(f"  - {k}: {desc}")
        else:
            present[k] = "***" if any(x in k for x in ("KEY", "SECRET", "PASSWORD", "TOKEN")) else v

    if missing and strict:
        msg = "Faltam variáveis obrigatórias no .env:\n" + "\n".join(missing)
        msg += f"\n\nCopie .env.example para .env e preencha. Arquivo esperado: {ROOT / '.env'} ou MKTFLOW/.env"
        raise RuntimeError(msg)

    if missing:
        # Aviso não-fatal (útil em dev/teste)
        sys.stderr.write("[config] Aviso: variáveis ausentes (pipeline P0 falhará se tentar publicar):\n" + "\n".join(missing) + "\n")

    return present

def validate_or_exit(required_keys=None):
    try:
        validate_env(strict=True, required_keys=required_keys)
    except RuntimeError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

if __name__ == "__main__":
    # Teste manual: python -m mkt_flow_p0.config
    try:
        validate_env(strict=True)
        print("OK: .env válido para P0")
    except RuntimeError as e:
        print(e)
        sys.exit(1)
