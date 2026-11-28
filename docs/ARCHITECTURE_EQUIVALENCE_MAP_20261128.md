# Mapa de equivalência arquitetural — 28/11/2026

Finalidade: apoiar decisões de higienização **sem excluir nada** enquanto não houver equivalência funcional comprovada e autorização.

Legenda: **COMPROVADO** = evidência direta; **RESOLVIDO** = suspeita esclarecida; **SUSPEITO** = exige prova; **PRESERVAR** = não remover.

## Itens esclarecidos nesta etapa

| Item | Resultado | Evidência |
|---|---|---|
| Cópia do registro assinado do Gate V1 (`gate_v1_registry_route.php`) | **RESOLVIDO** — difere apenas por quebra de linha final (CRLF + `\n`); `rstrip` dos bytes é idêntico | comparação local normalizada em 28/11 |
| `conexo_gate_trace.py` | **RESOLVIDO** — é o cliente dos endpoints `/editorial/trace/bind` e `/editorial/trace/event` implementados em `conexo-mkt-trace.php`; mesmos 11 estágios e schema `conexo-editorial-trace/1` | leitura dos dois lados; não é segundo ledger |

## Duplicações e sobreposições

| Item | Responsabilidade | Alternativa canônica | Situação | Prova necessária antes de remover |
|---|---|---|---|---|
| `editorial_trace.py` (`conexo-editorial-executor-events/1`) | trilha operacional, `run_id` e `content_sha256` | é a referência | **COMPROVADO / PRESERVAR** | — |
| `editorial_trace_turso.py` | outbox durável da trilha | referência de storage | **COMPROVADO / PRESERVAR** | — |
| `editorial_trace_gate.py` | consumidor que valida a trilha antes de publicar | referência de validação | **COMPROVADO / PRESERVAR** | — |
| `conexo-mkt-trace.php` | metade servidora no plugin Gate V1 | referência no WordPress | **COMPROVADO / PRESERVAR** | — |
| `editorial_gate_traceability.py` (sidecar) | preparação oficial para ASVE no Gate | referência versionada | **COMPROVADO / PRESERVAR** | — |
| `=true` | cópia da rota assinada | `gate_v1_registry_route.php` | **COMPROVADO / duplicata** | inventário classifica como `DUPLICATE`; manter até autorização |
| Ledgers do Gate V2 | terceiro sistema de recibos | Gate V1 RC10.4 + trilha única | **COMPROVADO / descontinuado** | não reativar; não remover sem decisão |
| Ledgers de tarefa do Conexo OS | recibos de coordenação, não editoriais | manter separados | **COMPROVADO / PRESERVAR** | nenhuma equivalência provada com a trilha editorial |
| Registro de fontes primárias em MKT-RSS e Conexo OS | mesma função, bytes idênticos | uma única cópia | **COMPROVADO / duplicata** | comparar hash após qualquer atualização antes de consolidar |
| Cópia vendorizada do Redator no MKT-RSS | dependência real de scripts e testes | repo autônomo do Bot Redator | **COMPROVADO / divergente** | diff controlado + suítes dos dois repos; `src/editorial/` existe só no repo autônomo |
| Três checkouts de `-site-conexotech` | plugins diferentes no mesmo remoto | um checkout por branch | **COMPROVADO / risco operacional** | conferir `branch --show-current` antes de qualquer ação |
| Nove dependências em `requirements/base.txt` com zero imports estáticos | possivelmente desnecessárias | perfil `requirements/rss.txt` | **SUSPEITO** | verificar imports dinâmicos; instalar em ambiente isolado e rodar suíte antes de mexer |
| Workflows órfãos do Gate V2 e workflows com arquivos inexistentes | automações antigas | executor isolado / Gate V1 | **COMPROVADO / órfãos** | checar histórico de execuções antes de desativar |

## Regra para qualquer remoção

1. localizar implementações;
2. mapear chamadores e dependências;
3. comparar contratos, entradas, saídas e efeitos colaterais;
4. criar teste de equivalência;
5. escolher a referência;
6. planejar migração reversível;
7. pedir autorização.

Nenhum arquivo, módulo, dependência ou branch foi excluído nesta etapa.

## Estado da etapa

**PARCIAL** — mapa pronto; remoções **NOT STARTED** e dependentes de autorização.
