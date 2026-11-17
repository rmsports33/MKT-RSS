# Configurar chaves de IA (Gemini / OpenRouter) — 17/11/2026

O motor `mkt_flow_p0/ai_providers.py` ja suporta: Groq (padrao), Gemini e
OpenRouter, com `AI_FREE_ONLY=true`, `AI_FALLBACK_ENABLED=false` e
`network_fallback=False`. Falta apenas a credencial para os dois ultimos.

## 1. Obtendo as chaves (no seu navegador, logado na sua conta)

### Gemini (Google AI Studio) — gratuito
1. Abra https://aistudio.google.com/app/apikey
2. Login com sua conta Google
3. Clique em **Create API key** (projeto novo ou existente)
4. Copie a chave (comeca com `AIza...`)
5. Modelos free sugeridos: `gemini-2.0-flash` / `gemini-1.5-flash`

### OpenRouter — gratuito
1. Abra https://openrouter.ai/keys
2. Login (GitHub ou Google)
3. Clique em **Create Key**
4. Copie a chave (comeca com `sk-or-...`)
5. Modelos free sugeridos: `google/gemini-2.0-flash:free`, `meta-llama/llama-3.3-70b-instruct:free`

⚠️ Nunca cole as chaves no chat, no GitHub ou em logs.

## 2. Configurando no servidor (Hostinger SSH)

As chaves devem ficar em arquivo privado, nunca em `.env` versionado nem no repo.
O padrao existente e `~/.config/conexo-os/` com permissao 0600.

> COMANDO PARA COPIAR E COLAR (cria o arquivo com permissao segura):

```bash
install -m 600 /dev/null ~/.config/conexo-os/ai-keys.env
```

> ABRA o arquivo com editor e adicione UMA linha por chave (sem aspas):

```bash
nano ~/.config/conexo-os/ai-keys.env
```

Conteudo (substitua pelos valores reais que você copiou):
```
GEMINI_API_KEY=AIza...sua_chave_aqui
OPENROUTER_API_KEY=sk-or-...sua_chave_aqui
GEMINI_MODEL=gemini-2.0-flash
OPENROUTER_MODEL=google/gemini-2.0-flash:free
```

## 3. Carregando as chaves no ambiente do executor

O `ai_providers.py` le `os.getenv(...)`. Para o Cron/controlador, exporte as
variaveis no mesmo processo. Opcoes:

### Opcao A — via `/etc/environment` ou `.bashrc` do usuario (persistente)
Adicione ao `~/.bashrc` do usuario `u401421381`:
```bash
set -a; . ~/.config/conexo-os/ai-keys.env; set +a
```
Isso carrega as chaves em cada sessao SSH e nos processos do Cron que usam bash.

### Opcao B — no wrapper do controlador (recomendado, escopo controlado)
Editar `ops/hostinger/run_remote.sh` para fazer `source` do arquivo antes de
executar o Python. (Aplica-se somente se o controlador precisar de IA; as acoes
de fila/Gate NAO precisam de IA.)

## 4. Validacao (sem expor chaves)

Depois de configurar,rode:

```bash
~/mkt-rss-runner/.venv/bin/python -c "
from mkt_flow_p0.ai_providers import provider_status
print(provider_status())
"
```

Esperado: `gemini` e `openrouter` com `configured: True`, `free: True`,
`fallback: False`.

## Notas
- Groq segue como padrao; nao alterar.
- Se uma chave falhar ou nao for free, o motor bloqueia (fail-closed) -- correto.
- Nenhuma chave deve ser commitada ou colada no chat.
