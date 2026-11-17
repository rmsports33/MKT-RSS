# Implantação segura da ação `queue_list` — 16/11/2026

Branch: `feat/hostinger-runtime-independente-20261113` (tip `e4482f5`)
Job solicitado: `queue-list-20261116-001` (ações `queue_list`, somente leitura).

Esta implantação **não publica, não escreve no WordPress nem altera o Gate**. Apenas
substitui dois arquivos no checkout privado `~/mkt-rss-runner` para que o Cron possa
listar os títulos `DESCOBERTA` e gerar o recibo de triagem.

## Hashes esperados (blobs da PR, SHA-256)

| Arquivo | SHA-256 |
|---|---|
| `ops/hostinger/remote_controller.py` | `17e38593914dcdc9bdab2cdf973df3eb982417bcf920baa20085fffc303ab622` |
| `ops/hostinger/remote_queue_bridge.py` | `c4e014bc0c090c351f4aa7d5c84362df2b4634ec2206b7e4ef4e70c376a8c71a` |

> **Nota sobre hashes:** estes são os SHA-256 dos **blobs do git (LF)**, que é o que
> o `git pull` grava no servidor Linux. Num checkout Windows os arquivos podem virar
> CRLF e gerar hashes diferentes — isso não é adulteração. No servidor Hostinger
> (Linux), `sha256sum` deve produzir exatamente os valores acima.

## Ordem obrigatória (evita queimar o `job_id`)

O `job_id` é de execução única. O controlador antigo não conhece `queue_list`; se o
Cron rodar com o controlador antigo e a requisição nova, ele falha fechado (`BLOCKED`)
e **não** queima o job. Ainda assim, valide a ponte com o virtualenv **antes** de trocar
o controlador, exatamente como no PR #123.

### 1. Atualizar o checkout (traz o código novo para o disco)

> COMANDO PARA COPIAR E COLAR no terminal da Hostinger, dentro de `~/mkt-rss-runner`:

```bash
cd ~/mkt-rss-runner && git fetch --no-tags origin feat/hostinger-runtime-independente-20261113 && git pull --ff-only origin feat/hostinger-runtime-independente-20261113
```

### 2. Fazer backup dos arquivos atuais

> COMANDO PARA COPIAR E COLAR:

```bash
mkdir -p ~/.local/state/conexo-os/queue-list-install-$(date -u +%Y%m%dT%H%M%SZ) && cp ops/hostinger/remote_controller.py ops/hostinger/remote_queue_bridge.py ~/.local/state/conexo-os/queue-list-install-$(date -u +%Y%m%dT%H%M%SZ)/
```

### 3. Validar a ponte nova com o virtualenv ANTES de trocar o controlador

> COMANDO PARA COPIAR E COLAR:

```bash
./.venv/bin/python -m py_compile ops/hostinger/remote_queue_bridge.py ops/hostinger/remote_controller.py && ./.venv/bin/python ops/hostinger/remote_queue_bridge.py --list
```

O `--list` deve retornar JSON com `"status": "PASS"`, `"mode": "READ_ONLY"`,
`"state": "DESCOBERTA"`, `"count": 20` e a lista de títulos. Isso prova que o
virtualenv tem as dependências do Turso antes de o Cron chamar o controlador.

### 4. Conferir os hashes instalados

> COMANDO PARA COPIAR E COLAR:

```bash
sha256sum ops/hostinger/remote_controller.py ops/hostinger/remote_queue_bridge.py
```

Compare com a tabela no topo. Os dois devem ser **idênticos**.

### 5. Verificar a requisição publicada

> COMANDO PARA COPIAR E COLAR:

```bash
git show origin/feat/hostinger-runtime-independente-20261113:ops/hostinger/remote_request.json
```

Deve mostrar:
```json
{"schema":"conexo-remote-request/1","job_id":"queue-list-20261116-001","action":"queue_list","article_ref":"rss-pautas"}
```

## Após a implantação

O Cron `*/5` processa o job em até 5 minutos. Verificar o recibo:

> COMANDO PARA COPIAR E COLAR:

```bash
cat ~/.local/state/conexo-os/remote-jobs/queue-list-20261116-001.json
```

Resultado esperado: `status=PASS`, `action=queue_list`, com `results[0].output`
contendo o JSON de `list_titles()` e os 20 títulos. Ticks seguintes devem responder
`ALREADY_PROCESSED` (idempotência por recibo durável).

Me envie o conteúdo do recibo que eu executo a triagem das 20 pautas.

## Reversão

Sem risco de escrita. Para reverter, restaurar os dois arquivos do backup
`~/.local/state/conexo-os/queue-list-install-*/` no checkout, sem tocar no banco,
Cron, Gate ou WordPress. Não apagar recibos processados.
