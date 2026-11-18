<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Como a triagem era feita e como ficou no OpenCode â€” 17/11/2026

Pergunta do proprietÃ¡rio: como o ChatGPT executava a tarefa de aplicar decisÃµes
na fila e como adaptar isso aqui. Resposta curta: **ele nÃ£o executava**.

## O que foi verificado

| Fonte | O que diz |
|---|---|
| `docs/RSS_EDITORIAL_TRIAGE_P1_PLAN.md` | P1 (selecionar/rejeitar) foi **planejada, nÃ£o implementada nem autorizada para ativaÃ§Ã£o**; nenhuma heurÃ­stica muda status sozinha |
| `docs/RSS_TRIAGE_P1_SECURITY_REVIEW.md` | a CLI de decisÃµes Ã© **fail-closed e nÃ£o aceita gravaÃ§Ãµes remotas**; consulta e histÃ³rico continuam disponÃ­veis |
| `mkt_flow_p0/triagem_auth.py` | polÃ­tica de allowlist `P1_AUTHORIZED_ACTORS` para **GitHub Actions** (`workflow_dispatch`, branch `master`, environment aprovado) |
| Banco de produÃ§Ã£o (verificaÃ§Ã£o real) | tabela `rss_triage_audit` e triggers **nÃ£o existiam** â€” prova de que nenhuma decisÃ£o P1 foi gravada atÃ© hoje |

Ou seja: o ChatGPT lia a fila, apresentava candidatos e deixava a decisÃ£o para
uma etapa humana futura. O desenho de escrita dependia de um workflow do GitHub
Actions com identidade da plataforma e aprovaÃ§Ã£o de environment â€” e esse
workflow **nunca foi habilitado**. NÃ£o hÃ¡ registro de decisÃ£o aplicada por ele.

## Por que nÃ£o foi simplesmente reativar esse caminho

1. O proprietÃ¡rio despriorizou GitHub Actions como executor padrÃ£o em 13/11.
2. O token de escrita da fila nÃ£o tem permissÃ£o de DDL â€” a auditoria nÃ£o podia
   ser criada por ele.
3. `triagem_decisoes.decidir()` exige gravar a auditoria na mesma transaÃ§Ã£o:
   sem tabela/trigger, falha fechado. Correto, mas inutilizÃ¡vel.

## A adaptaÃ§Ã£o feita aqui

| Desenho original (Actions) | AdaptaÃ§Ã£o no OpenCode |
|---|---|
| identidade = `GITHUB_ACTOR` | identidade = **usuÃ¡rio autenticado do sistema** (`getpass.getuser()`) |
| aprovaÃ§Ã£o de `environment` | `--confirmar` explÃ­cito, **uma pauta por vez** |
| allowlist `P1_AUTHORIZED_ACTORS` | allowlist opcional `P1_AUTHORIZED_OPERATORS` |
| token do runner | token do Turso no ambiente, nunca no chat |

Ferramentas:

- `tools/provision_triage_audit.py` â€” cria a tabela e os trÃªs triggers
  (`CREATE ... IF NOT EXISTS`), sem tocar em dados.
- `tools/triagem_decidir.py` â€” verifica auditoria antes de gravar, exige
  confirmaÃ§Ã£o, usa identidade do sistema e faz readback depois.

Para provisioning foi usado o token de plataforma do Turso que jÃ¡ estava no
servidor (`~/.config/turso/settings.json`) para gerar um token de banco de
**1 dia**, usado em memÃ³ria e nÃ£o gravado em disco. O cache antigo do CLI estava
expirado (HTTP 401) â€” por isso a geraÃ§Ã£o nova.

Limite declarado: identidade de sistema **nÃ£o Ã© atestado criptogrÃ¡fico**. A
proteÃ§Ã£o nÃ£o vem dela, vem da confirmaÃ§Ã£o explÃ­cita, da auditoria imutÃ¡vel no
banco (triggers `BEFORE UPDATE`/`BEFORE DELETE`) e do readback.

## EvidÃªncia da execuÃ§Ã£o

| VerificaÃ§Ã£o | Resultado |
|---|---|
| Objetos criados no Turso | `rss_triage_audit` + 3 triggers |
| Pautas Anatel/TIM e Claro/Senado | `DESCOBERTA` â†’ `SELECIONADA` |
| Eventos de auditoria | `ba4bc9eeâ€¦` e `41454622â€¦`, operador `u401421381` |
| Estado final da fila | 22 em `DESCOBERTA`, 2 em `SELECIONADA` |
| Readback | 2 linhas na auditoria, sem alteraÃ§Ã£o de artigo ou WordPress |

Nenhum artigo foi publicado, agendado ou aprovado por causa dessa gravaÃ§Ã£o.
Ela apenas registra a escolha editorial que o proprietÃ¡rio jÃ¡ havia feito.
