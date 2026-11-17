# Como a triagem era feita e como ficou no OpenCode — 17/11/2026

Pergunta do proprietário: como o ChatGPT executava a tarefa de aplicar decisões
na fila e como adaptar isso aqui. Resposta curta: **ele não executava**.

## O que foi verificado

| Fonte | O que diz |
|---|---|
| `docs/RSS_EDITORIAL_TRIAGE_P1_PLAN.md` | P1 (selecionar/rejeitar) foi **planejada, não implementada nem autorizada para ativação**; nenhuma heurística muda status sozinha |
| `docs/RSS_TRIAGE_P1_SECURITY_REVIEW.md` | a CLI de decisões é **fail-closed e não aceita gravações remotas**; consulta e histórico continuam disponíveis |
| `mkt_flow_p0/triagem_auth.py` | política de allowlist `P1_AUTHORIZED_ACTORS` para **GitHub Actions** (`workflow_dispatch`, branch `master`, environment aprovado) |
| Banco de produção (verificação real) | tabela `rss_triage_audit` e triggers **não existiam** — prova de que nenhuma decisão P1 foi gravada até hoje |

Ou seja: o ChatGPT lia a fila, apresentava candidatos e deixava a decisão para
uma etapa humana futura. O desenho de escrita dependia de um workflow do GitHub
Actions com identidade da plataforma e aprovação de environment — e esse
workflow **nunca foi habilitado**. Não há registro de decisão aplicada por ele.

## Por que não foi simplesmente reativar esse caminho

1. O proprietário despriorizou GitHub Actions como executor padrão em 13/11.
2. O token de escrita da fila não tem permissão de DDL — a auditoria não podia
   ser criada por ele.
3. `triagem_decisoes.decidir()` exige gravar a auditoria na mesma transação:
   sem tabela/trigger, falha fechado. Correto, mas inutilizável.

## A adaptação feita aqui

| Desenho original (Actions) | Adaptação no OpenCode |
|---|---|
| identidade = `GITHUB_ACTOR` | identidade = **usuário autenticado do sistema** (`getpass.getuser()`) |
| aprovação de `environment` | `--confirmar` explícito, **uma pauta por vez** |
| allowlist `P1_AUTHORIZED_ACTORS` | allowlist opcional `P1_AUTHORIZED_OPERATORS` |
| token do runner | token do Turso no ambiente, nunca no chat |

Ferramentas:

- `tools/provision_triage_audit.py` — cria a tabela e os três triggers
  (`CREATE ... IF NOT EXISTS`), sem tocar em dados.
- `tools/triagem_decidir.py` — verifica auditoria antes de gravar, exige
  confirmação, usa identidade do sistema e faz readback depois.

Para provisioning foi usado o token de plataforma do Turso que já estava no
servidor (`~/.config/turso/settings.json`) para gerar um token de banco de
**1 dia**, usado em memória e não gravado em disco. O cache antigo do CLI estava
expirado (HTTP 401) — por isso a geração nova.

Limite declarado: identidade de sistema **não é atestado criptográfico**. A
proteção não vem dela, vem da confirmação explícita, da auditoria imutável no
banco (triggers `BEFORE UPDATE`/`BEFORE DELETE`) e do readback.

## Evidência da execução

| Verificação | Resultado |
|---|---|
| Objetos criados no Turso | `rss_triage_audit` + 3 triggers |
| Pautas Anatel/TIM e Claro/Senado | `DESCOBERTA` → `SELECIONADA` |
| Eventos de auditoria | `ba4bc9ee…` e `41454622…`, operador `u401421381` |
| Estado final da fila | 22 em `DESCOBERTA`, 2 em `SELECIONADA` |
| Readback | 2 linhas na auditoria, sem alteração de artigo ou WordPress |

Nenhum artigo foi publicado, agendado ou aprovado por causa dessa gravação.
Ela apenas registra a escolha editorial que o proprietário já havia feito.
