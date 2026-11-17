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
