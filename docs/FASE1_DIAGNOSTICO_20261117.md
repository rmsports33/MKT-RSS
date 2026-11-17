# Fase 1 — Diagnóstico de execução — 17/11/2026

Escopo: M10 (proteção anti-auto-deploy) e M09 (erro JS `main.js`).
Repo afetado: `rmsports33/-site-conexotech` (privado), **não** MKT-RSS.

Nenhuma alteração foi feita em produção, tema, workflow ou arquivos do site.

## M10 — Proteção anti-auto-deploy: ✅ JÁ INTEGRADA EM MASTER

Verificação direta de `.github/workflows/auto-deploy.yml` (ref `master`):
- `workflow_dispatch:` presente (gatilho manual)
- `aplicar:` com `default: false`
- `if: success() && inputs.aplicar == true`
- `if [ "${{ inputs.aplicar }}" = "true" ]`
- **Sem `cron:` e sem `push:`**

Conclusão: os 7 invariantes da Issue #51 já estão no código de master. A Issue
permanece **aberta no GitHub**, mas a proteção está implementada. **M10 pode ser
marcado como resolvido** — não é necessário reimplementar nem reabrir o PR #51
(que está em branch `safety/guard-auto-deploy-manual-only`, sha `349c9ba5`).

⚠️ Ressalva do próprio issue #51: pipelines externos (mirror GitLab em
`espelho-gitlab.yml`) podem disparar em push a master. A proteção cobre o
`auto-deploy.yml`, não esse espelhamento. Verificar antes de qualquer merge.

## M09 — Erro JS `main.js`: ⛔ BLOQUEADO POR ARTEFATO ILEGÍVEL NO REPO

Achado crítico: `conexotech/main.js` no repo `-site-conexotech` **não é texto JavaScript**.

| Ref | Tamanho | Conteúdo |
|-----|---------|----------|
| `master` | 72 bytes | bytes binários (`\x99\xeb,j\x07...`) |
| `fix/mobile-guide-9798-theme-js-20261111` (PR #71) | 72 bytes | mesmos bytes binários |
| `fix/main-js-csv-closure` (PR #50) | (branch separada) | — |

Ou seja: o `main.js` versionado é um placeholder/artefato corrompido em ambas as
refs. O JS **real** existe apenas no servidor da Hostinger — exatamente como o
Issue #71 registra: *"arquivos do tema versionados divergem previamente da master;
aplicar somente o delta aos arquivos correntes, nunca substituir o tema inteiro."*

### Consequência

Não é possível aplicar a correção da linha 230 (`csvBtns.forEach` → `});`)
a partir do repositório: não há texto-fonte para delta. Qualquer tentativa de
"copiar do repo para o servidor" **substituiria o JS real por 72 bytes binários
e quebraria o tema**.

### PRs relacionados (todos OPEN, base master)

| PR | Branch | Sha | Conteúdo útil |
|----|--------|-----|---------------|
| #71 | `fix/mobile-guide-9798-theme-js-20261111` | `ec5c27b7` | `style.css` (33 KB) e `functions.php` (65 KB) legítimos; main.js ilegível |
| #51 | `safety/guard-auto-deploy-manual-only` | `349c9ba5` | proteção **já em master** |
| #50 | `fix/main-js-csv-closure` | `1e98583e` | correção de sintaxe (branch própria) |

## O que é seguro fazer (sem servidor)

1. ✅ Marcar M10 como resolvido (proteção já em master).
2. ⛔ **Não** mesclar PR #71/#50 nem copiar `main.js` do repo para o servidor.
3. 📋 Registrar que a correção do JS exige leitura do arquivo real via SSH.

## ✅ Resolução aplicada em 17/11/2026

O operador executou no servidor, via SSH:
1. Backup: `cp main.js main.js.bak-20261117`
2. Correção: `sed -i '230s/^  }$/  });/' main.js`
3. Verificação: linha 230 passou a ser `  });`
4. Validação de sintaxe (sem `node` no servidor) via Python:
   - parênteses `()` 192/192 OK
   - chaves `{}` 65/65 OK
   - colchetes `[]` 13/13 OK
5. Versões coerentes: `CONEXO_VERSION = 1.6.9`, `Version: 1.6.9` (style.css)

**Resultado:** M09 resolvido no arquivo corrente do servidor. M10 já estava
resolvido em master. Fase 1 concluída.

⚠️ **Não mesclar PR #71 nem PR #50**: o `main.js` do repo é artefato binário;
aplicar esses PRs substituiria o JS real por 72 bytes corrompidos. A correção
foi feita apenas no servidor, com backup.

## ✅ Reconciliação repo ↔ servidor (17/11/2026)

A divergência foi **eliminada na raiz**: o JS real do servidor foi trazido para o repo.

- O operador gerou `base64 -w0` do `main.js` em produção (via SSH, leitura).
- Decodificação local: **8.656 bytes**, UTF-8 válido, SHA-256
  `9afeaaa28caff772bad71e44a19a52d83c5b3f366f2a38be18032f0be4e79cc2` —
  **idêntico ao SHA-256 do arquivo no servidor**.
- Validação: parênteses 192/192, chaves 65/65, colchetes 13/13; linha 230 = `  });`; 254 linhas.
- O blob commitado foi conferido byte-a-byte (8656 bytes, mesmo SHA).
- Branch `fix/reconcile-main-js-20261117` no repo privado, commit `09b3868`.
- **PR #78** aberto para revisão (`fix(theme): reconcile main.js with live server`).
- Os PRs #71 e #50 podem ser fechados como obsoletos quando o proprietário aprovar.

**Resultado:** o repo passa a refletir exatamente o JS que roda em produção, com a
correção da linha 230. Nenhum deploy automático (proteção da issue #51 já em master).
Nenhuma credencial exposta. Nenhuma alteração em produção além da linha 230 (já validada).

## Próximo passo (depende de SSH — operador)

> COMANDO PARA COPIAR E COLAR no terminal da Hostinger (somente leitura):

```bash
find ~/ -path '*/wp-content/themes/*' -name main.js -type f 2>/dev/null | head -5
```

Depois, para localizar a linha problemática:

```bash
grep -n "csvBtns.forEach" CAMINHO_DO_MAIN.js
```

Com o caminho e o trecho reais, o delta pode ser preparado com segurança e
aplicado **somente ao arquivo corrente do servidor**, com backup prévio.
