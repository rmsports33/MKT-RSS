# Implantação segura da ação `binance_stage` — 17/11/2026

Branch operacional: `feat/hostinger-runtime-independente-20261113` @ `7e0c0f0`
Issue: MKT-RSS #121. Código implementado e **corrigido**, **não executado**.

## ⚠️ ATUALIZAÇÃO CRÍTICA (17/11) — pré-condições reais descobertas no servidor

A investigação no servidor revelou que o `binance_stage` **não pode executar ainda**:

1. **Não existe pacote `editorial-workflow/2` no servidor.** O handoff
   `binance-revisao-48f1ea5be313` contém apenas `conexo-editorial-handoff/1`
   (`metadata` + `markdown`) — que **não é entrada do Gate**. O validator do core
   exige `substantive_review`, `sources`, `claims`, `images`, `human`, etc., que só
   o pipeline supervisionado (com IA) produz. O script foi corrigido para
   **rejeitar o handoff e exigir o pacote real** (`PUBLISHABLE_PACKAGE_MISSING`),
   sem sintetizar nada localmente.
2. **O core editorial não está instalado.** `scripts/editorial_write.py`
   (commit `b485d91`, SHA-256 `823d97d5...`) não existe em nenhum `$HOME`.
3. **Credenciais** ficam em `~/.config/conexo-os/wp-editorial.token` — o script
   foi ajustado para ler esse arquivo (não apenas env vars).

### Consequência
**NÃO publicar o `remote_request.json` agora.** O `job_id` está preservado.

### ✅ Atualização 17/11 (continuação) — core instalado

O core editorial foi instalado com sucesso em
`~/.cache/conexo-os/editorial-core/` via SCP, com os 5 arquivos nas subpastas
corretas (`scripts/`, `docs/`) e **todos os SHA-256 verificados** contra o lock:
```
823d97d5...  scripts/editorial_write.py
bf6755e6...  scripts/validate_editorial_package.py
e29bbd26...  AGENTS.md
cfb2408d...  docs/EDITORIAL_DNA_V1.md
bf7382bd...  docs/EDITORIAL_WORKFLOW.md
```
`load_core()` aceitará este checkout. O script `binance_gate_stage.py` já descobre
este caminho automaticamente (`_find_core` procura `~/.cache/conexo-os/editorial-core`).

**Bloqueio restante (o fundamental): o pacote `editorial-workflow/2`.**
O handoff `conexo-editorial-handoff/1` (metadata+markdown) não é entrada do Gate;
o validador exige `substantive_review`, `sources`, `claims`, `images`, `human`,
`editorial_decision`, `process_steps`, `keyword_research` etc., produzidos pelo
pipeline supervisionado. Ação correta: gerar o pacote pelo pipeline e só então
publicar a requisição. Nada foi queimado.

---

## (Seção original — mantida para referência)

Issue: MKT-RSS #121. Código implementado, **não executado**. Nenhuma credencial
no repo; nenhuma publicação; nenhuma aprovação.

## O que a ação faz
Cria o rascunho Binance **exclusivamente pela rota canônica do Gate**
(`editorial/write` via `publish_package(intent="stage")`), com:
- versão exata `d2ccb99e...` e markdown `1969799c...` verificados do handoff imutável
- `featured_media = 9892` associado somente ao novo rascunho
- um único receipt por hash (idempotência), sem retry automático
- `publication_authorized=false`, `human_acceptance=PENDING`
- proibido: REST genérico `wp/v2/posts`, `wpcom_mcp_posts_create`, token no código

## Arquivos novos/alterados
| Arquivo | SHA-256 (blob git, LF) |
|---|---|
| `ops/hostinger/binance_gate_stage.py` | `4adb8f363f471963c4b1d9fcaf80da938a5f7c11b266d42d9f2441b062bfa35a` |
| `ops/hostinger/conexo_editorial.sh` | `7175084a2f9b6d950cc702a171c40d2c9667c40cfa5296f1999d9d7f9d5e490d` |
| `ops/hostinger/remote_controller.py` | `d0524f624d967c73ab5d0c036578d6468c77d37e8e5306888755de74ff09f1e6` |
| `tests/test_binance_gate_stage.py` | 6 testes de contrato |

## Pré-condições (verificar ANTES de implantar)

> COMANDOS PARA COPIAR E COLAR no terminal da Hostinger (somente leitura):

```bash
# 1. Handoff existe e é íntegro
ls -la /home/u401421381/.local/share/conexo-os/handoffs/binance-revisao-48f1ea5be313

# 2. Mídia 9892 existe e está livre
#    (via WordPress REST autenticado existente)

# 3. Core editorial fixado por hash existe no checkout
find ~/ -path '*conexo-os-core*' -name editorial_write.py 2>/dev/null | head -3

# 4. Credenciais WP do operador disponíveis no ambiente (não no repo)
#    confirmar que WP_USER/WP_APP_PASSWORD existem no ambiente privado
```

## Ordem de implantação (evita queimar o job_id)

1. Atualizar checkout: `git pull --ff-only origin feat/hostinger-runtime-independente-20261113`
2. Fazer backup dos 3 arquivos alterados
3. Validar com o virtualenv ANTES de trocar o controlador:
   ```bash
   ./.venv/bin/python -m py_compile ops/hostinger/binance_gate_stage.py ops/hostinger/remote_controller.py
   ./.venv/bin/python -m pytest -q tests/test_binance_gate_stage.py
   ```
4. Conferir SHA-256 dos arquivos instalados
5. **Só depois** criar o `remote_request.json` com o novo job_id:
   ```json
   {"schema":"conexo-remote-request/1","job_id":"binance-stage-20261117-001","action":"binance_stage","article_ref":"binance-revisao-6e8da0b05713"}
   ```
6. O Cron processa em até 1 minuto. Verificar recibo:
   ```bash
   cat ~/.local/state/conexo-os/remote-jobs/binance-stage-20261117-001.json
   ```

## Regras
- Se o core fixado por hash não existir, a ação falha fechado (`TRUSTED_CORE_MISSING`).
- Se as credenciais WP não estiverem no ambiente, falha fechado (`WP_CREDENTIALS_MISSING`).
- Qualquer falha de staging é **não repetível** por design; novo job_id exige nova decisão.
- Não publicar, não agendar, não alterar #9708/#9744.
- Aprovação humana da versão continua obrigatória no Gate; este fluxo só cria o rascunho `draft`.
