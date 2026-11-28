# Registro de fechamento — 28/11/2026

Registro atualizado após auditoria cruzada dos quatro PRs e leitura direta dos contratos e caminhos de integração. Nenhuma alteração funcional, nenhuma operação de produção, nenhum merge ou deploy.

## Referências atuais

| PR | SHA atual verificado | Estado |
|---|---|---|
| Gate V1 #91 — `rmsports33/-site-conexotech` | `2b7180fa3de66b644372d3661a392852e728661c` | aberto, draft, não merged |
| MKT-RSS #142 — `rmsports33/MKT-RSS` | `b8282af70b3887cad54d006089bcc7e226124220` | aberto, draft, não merged |
| Bot Redator #6 — `rmsports33/bot-redator-artigo` | `418be3556d15c001e5882e8c345626b0d78ea138` | aberto, draft, não merged |
| Conexo OS #86 — `rmsports33/conexo-os` | `c22f1dd8b2e9dc8d5065261928a8f61ecf51ed3c` | aberto, draft, não merged |

O SHA `31a511e0ab4d5e00c2db3912a0f6a5edada33485` continua como referência histórica dos sete documentos inicialmente verificados. O SHA `9c08142b6b971d53c000f67c049def2d16fb4cbd` foi o head anterior à correção da especificação. O head atual do PR #142 é `b8282af`.

## Validações já comprovadas

### Gate V1 — SHA exato `2b7180f`

Checkout limpo. Ambiente: Windows, Python 3.14.7, pytest 9.1.1 — não é Linux.

```
test_conjunto_versionado_reproduz_artefato_instalado PASSED
test_excecoes_estao_declaradas                        PASSED
test_substituicao_de_credenciais_e_fail_closed        PASSED
test_identidade_do_executor_autorizado                 PASSED
test_rejeicao_de_demais_cenarios                       PASSED
test_uuid_autorizado_ausente_ou_vazio                  PASSED
test_funcao_de_app_password_indisponivel               PASSED
7 passed
```

A ressalva anterior dos dois testes de drift está resolvida. O PASS é local e não cobre produção nem Linux.

### Contrato editorial e catálogo

Comparação direta dos arquivos nos heads de Conexo OS #86 e MKT-RSS #142:
- JSON do contrato: conteúdo idêntico após excluir apenas o campo declarativo `contract_sha256`.
- Catálogo de fontes primárias: conteúdo idêntico.
- Hash canônico declarado: `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

Isso comprova sincronização dos artefatos versionados, não execução integrada dos consumidores.

## Auditoria cruzada — bloqueios técnicos encontrados

1. **Três artefatos do Gate não podem ser confundidos.** O parecer de qualidade (`/quality/record`), a aprovação humana (`/review/approve`) e o envelope HMAC de escrita (`/editorial/write`) têm contratos distintos. O executor `wp_quality_executor.py` registra o parecer, mas não gera/submete o envelope HMAC de escrita.
2. **ASVE ainda não chega ao consumidor Gate.** O sidecar `editorial_gate_traceability.py` é produzido e validado no MKT-RSS, mas os testes e o contrato registram que `cxeg-package:v1` não o consome. A trilha ASVE está preparada, não integrada ao Gate.
3. **Scoring 0–100 não está ligado ao executor WordPress.** `wp_quality_executor.py` importa o Revisor Único legado; não chama `editorial_quality_score.py`. O scoring aparece no fluxo de importação/offline. O contrato mantém escala não confirmada e limiar nulo.
4. **Escrita condicional existe parcialmente no Gate V1.** O código do PR #91 tem lock por post, `expected_sha256`, nonce/idempotência e readback. Isso protege chamadas pela rota Gate, mas ainda exige prova contra escrita REST direta concorrente e falha parcial entre `wp_insert_post` e atualização de metadado. Não criar uma segunda função antes de testar e fechar essas lacunas.
5. **O pacote ASVE precisa de extensão compatível e fail-closed**, sem criar outro ledger e sem transformar ASVE em aprovação humana ou autorização de publicação.

A especificação `docs/PRODUCTION_INTEGRATION_SPEC_20261128.md` foi corrigida para refletir esses fatos no commit `b8282af70b3887cad54d006089bcc7e226124220`. A descrição do PR #142 também foi atualizada para não sugerir trabalho com Gate V2.

## Evidências ainda não executadas nos SHAs atuais

- MKT-RSS #142: os 46 novos casos de teste descritos no PR não foram executados no head atual. Os 17 testes de scoring/golden set pertencem a execução anterior e não são atribuídos a este SHA.
- Bot Redator #6: os três novos testes do contrato de prompt não têm execução comprovada no SHA atual; os 143 testes anteriores não substituem essa validação. Linux continua pendente.
- Conexo OS #86: `py_compile` isolado do sincronizador foi reportado; testes de runtime não estão comprovados. O status de Actions foi `failure` sem logs/etapas disponíveis; não foi usado como executor nem interpretado como falha de código.
- Gate V1 #91: sete testes locais aprovados no SHA exato. O status espelho de Actions aparece como `failure`; não foi usado como executor.
- MKT-RSS #142: sem execução de workflow registrada para o SHA consultado.

Não foi possível executar as suítes nesta sessão: o ambiente de execução disponível não tem acesso de rede ao GitHub para clonar os repositórios, e não há sessão/workspace OpenCode ou Railway conectada. Nenhum sandbox pago ou novo executor foi criado. Isso não substitui nem invalida a execução local pendente do OpenCode.

## Estado de conclusão

| Frente | Estado |
|---|---|
| Gate V1 — sete testes locais | Concluído |
| Sincronização contrato/catálogo Conexo OS ↔ MKT-RSS | Concluído |
| Sete documentos originais em `31a511e` | Concluído |
| Especificação reconciliada no PR #142 | Concluído |
| Homologação dos quatro PRs | Pendente |
| ASVE integrada ao contrato consumido pelo Gate | Pendente |
| Scoring 0–100 no executor WordPress/Gate | Pendente |
| Testes completos do MKT-RSS no SHA atual | Pendente |
| Testes do Bot Redator no SHA atual e em Linux | Pendente |
| Testes de runtime do Conexo OS #86 | Pendente |
| Readback autenticado real | Pendente |
| Envelope HMAC de escrita válido para versão atual | Pendente |
| Escrita condicional contra bypass REST e falha parcial | Pendente |
| Parecer humano do artigo #9925 e piloto A/B cego | Pendente |
| Higienização arquitetural com provas de equivalência | Parcial |
| Produção, merge, deploy, ativação e publicação | Não executados |

## Próximas execuções técnicas sem intervenção do proprietário

1. No OpenCode, checkout exato dos heads atuais e execução das suítes focadas descritas no runbook, sem Actions/CircleCI e sem credenciais.
2. Corrigir falhas encontradas nos testes, com regressão mínima e completa, preservando alterações preexistentes.
3. Implementar a extensão do pacote Gate V1 para consumir recibo ASVE e decisões versionadas, com testes de compatibilidade e rejeição fail-closed.
4. Integrar o scoring ao executor WordPress como evidência diagnóstica, mantendo os 13 checks humanos e o aceite separado; não definir limiar editorial sem decisão do proprietário.
5. Fechar as provas de concorrência e falha parcial do writer existente, incluindo tentativa de escrita REST fora da rota Gate.
6. Executar piloto A/B técnico com fixtures existentes; avaliação humana e decisão editorial continuam sendo dependências humanas.
7. Validar o sincronizador Conexo OS e a portabilidade Linux, sem criar infraestrutura paga.

Nenhuma mudança de status será atribuída sem execução e evidência no SHA correspondente. Gate V2 permanece descontinuado.