# Registro de fechamento — 28/11/2026

Registro atualizado após auditoria cruzada dos quatro PRs e execução técnica local integrada. Nenhuma operação de produção, nenhum merge, deploy, ativação ou provisionamento.

## Referências atuais

| PR | SHA atual verificado | Estado |
|---|---|---|
| Gate V1 #91 — `rmsports33/-site-conexotech` | `3a74c289fcbd36d5f51cd3c6a3fd72be3beffc46` | aberto, draft, não merged |
| MKT-RSS #142 — `rmsports33/MKT-RSS` | `fceb66e9088e20dbc806a8e8a95c667b385f9dca` (head funcional; o commit que contém este registro atualiza apenas documentação) | aberto, draft, não merged |
| Bot Redator #6 — `rmsports33/bot-redator-artigo` | `418be3556d15c001e5882e8c345626b0d78ea138` | aberto, draft, não merged |
| Conexo OS #86 — `rmsports33/conexo-os` | `c22f1dd8b2e9dc8d5065261928a8f61ecf51ed3c` | aberto, draft, não merged |

O SHA `31a511e0ab4d5e00c2db3912a0f6a5edada33485` continua como referência histórica dos sete documentos inicialmente verificados. O SHA `9c08142b6b971d53c000f67c049def2d16fb4cbd` foi o head anterior à correção da especificação; `b8282af` contém a especificação reconciliada. Esta versão do registro acompanha o head do branch, portanto o SHA exato do head deve ser lido diretamente no PR antes de qualquer execução.

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

### Execução técnica integrada — SHAs atuais

- **Gate V1 #91, SHA `491061f`:** checkout limpo clonado do GitHub; 8 testes aprovados em `tests/test_gate_v1_drift.py`, incluindo o novo teste de identidade do revisor; PHP lint 0 falhas. Inventário: 17 `MATCH`, 2 divergências documentadas, 1 credencial, 1 duplicata, 0 inexplicadas. Correção: `cxeg_review_identity_valid()` passou a rejeitar autor, proprietário em modo independente, conta de serviço configurada e identidade canônica do broker.
- **MKT-RSS #142, SHA funcional `4e94f09`:** 39 testes focados aprovados (20 subtests) em `test_wp_quality_executor.py`, `test_editorial_quality_score.py` e `test_editorial_golden_set.py`. A nota 0–100 passou a ser anexada ao parecer como diagnóstico, com `fingerprint` e `content_sha256` do texto lido; não substitui o Revisor Único nem autoriza publicação.
- **MKT-RSS, suíte completa no SHA `acecf02`:** 1540 aprovados, 1 ignorado, 72 subtests; 8 falhas por `PermissionError [WinError 32]` ao limpar diretórios temporários no Windows. Não é falha funcional comprovada, mas impede declarar suíte verde neste ambiente. Não foi repetida após `4e94f09`.
- **Conexo OS #86, SHA `c22f1dd`:** 154 aprovados, 1 ignorado, 69 subtests. Nenhuma credencial real usada.
- **Bot Redator #6, SHA `418be35`:** não repetido; evidência anterior preservada. Linux continua sem ambiente disponível.

### Contrato editorial e catálogo

Comparação direta dos arquivos nos heads de Conexo OS #86 e MKT-RSS #142:
- JSON do contrato: conteúdo idêntico após excluir apenas o campo declarativo `contract_sha256`.
- Catálogo de fontes primárias: conteúdo idêntico.
- Hash canônico declarado: `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

Isso comprova sincronização dos artefatos versionados, não execução integrada dos consumidores.

## Auditoria cruzada — bloqueios técnicos encontrados

1. **Três artefatos do Gate não podem ser confundidos.** O parecer de qualidade (`/quality/record`), a aprovação humana (`/review/approve`) e o envelope HMAC de escrita (`/editorial/write`) têm contratos distintos. O executor `wp_quality_executor.py` registra o parecer e não gera envelope — separação intencional. O envelope existe no caminho de publicação (`editorial_transport.py` → `core.prepare_write`), com chave externa e núcleo verificado por hash; 10 testes focados aprovados em `test_editorial_transport.py` e `test_publish_owner_approved.py` comprovam o formato e o readback com núcleo sintético. Não foi criado segundo adaptador HMAC; falta apenas prova com chave e WordPress reais, o que depende de produção.
2. **ASVE ainda não chega ao consumidor Gate.** O sidecar `editorial_gate_traceability.py` é produzido e validado no MKT-RSS, mas os testes e o contrato registram que `cxeg-package:v1` não o consome. A trilha ASVE está preparada, não integrada ao Gate.
3. **Scoring 0–100 integrado como diagnóstico, mas ainda não consumido pelo Gate.** `wp_quality_executor.py` passou a anexar o recibo ao parecer, vinculado ao fingerprint e ao hash exatos. O Gate ainda não consome esse campo; escala e limiar continuam sem confirmação editorial.
4. **Escrita condicional existe parcialmente no Gate V1.** O código do PR #91 tem lock por post, `expected_sha256`, nonce/idempotência e readback. Isso protege chamadas pela rota Gate, mas ainda exige prova contra escrita REST direta concorrente e falha parcial entre `wp_insert_post` e atualização de metadado. Não criar uma segunda função antes de testar e fechar essas lacunas.
5. **O pacote ASVE precisa de extensão compatível e fail-closed**, sem criar outro ledger e sem transformar ASVE em aprovação humana ou autorização de publicação.\n6. **Identidade humana do revisor reforçada e testada.** `cxeg_review_identity_valid()` agora rejeita autor, proprietário em modo independente, conta de serviço configurada e identidade canônica do broker; o modo owner continua separado. Nove casos sintéticos aprovados no SHA `491061f`. Ainda depende de confirmação humana das identidades autorizadas reais.

A especificação `docs/PRODUCTION_INTEGRATION_SPEC_20261128.md` foi reconciliada no commit `b8282af70b3887cad54d006089bcc7e226124220` e recebeu correção adicional no commit `7301914b3e11ef4b331fdb527d778ea26e5eb5cb`: o executor WordPress já anexa a nota diagnóstica 0–100 ao parecer, vinculada ao fingerprint e ao hash do texto; o Gate ainda não a consome semanticamente. A descrição do PR #142 também foi atualizada para não sugerir trabalho com Gate V2.

## Evidências ainda não executadas nos SHAs atuais

- MKT-RSS #142: a suíte completa foi executada em `acecf02`, não no head que contém este registro; 8 falhas de limpeza de arquivo temporário no Windows permanecem sem correção. Não repetir sem necessidade.
- Bot Redator #6: os testes do contrato de prompt não foram reexecutados nesta rodada; a evidência anterior de 143 testes permanece separada. Linux continua sem ambiente disponível.
- Gate V1 #91: oito testes aprovados em checkout limpo no SHA `491061f`; o status espelho de Actions falha por cobrança e não foi usado como executor.
- Integração ponta a ponta com WordPress efêmero, envelope HMAC e recibo ASVE consumido pelo Gate: **não executada**. Não há plugin ativo descartável nem chave de teste provisionada; criar isso exigiria produção ou nova infraestrutura.

Nenhum sandbox pago, Actions ou CircleCI foi criado ou usado. As execuções acima foram locais, com dados sintéticos e sem credenciais reais.

## Estado de conclusão

| Frente | Estado |
|---|---|
| Gate V1 — oito testes locais no SHA `491061f` | Concluído |
| Sincronização contrato/catálogo Conexo OS ↔ MKT-RSS | Concluído |
| Sete documentos originais em `31a511e` | Concluído |
| Especificação reconciliada no PR #142 | Concluído |
| Homologação dos quatro PRs | Pendente |
| ASVE integrada ao contrato consumido pelo Gate | Pendente |
| Scoring 0–100 como diagnóstico no executor WordPress | Concluído |
| Consumo do scoring e da ASVE pelo Gate | Pendente |
| Testes completos do MKT-RSS no SHA atual | Parcial — 8 falhas de ambiente no Windows |
| Testes do Bot Redator no SHA atual e em Linux | Pendente |
| Testes de runtime do Conexo OS #86 | Concluído |
| Identidade humana do revisor separada da conta de serviço | Concluído |
| Teste integrado ponta a ponta com WordPress efêmero | Não iniciado |
| Readback autenticado real | Pendente |
| Envelope HMAC de escrita válido para versão atual | Pendente |
| Escrita condicional contra bypass REST e falha parcial | Pendente |
| Parecer humano do artigo #9925 e piloto A/B cego | Pendente |
| Higienização arquitetural com provas de equivalência | Parcial |
| Produção, merge, deploy, ativação e publicação | Não executados |

## Próximas execuções técnicas sem intervenção do proprietário

1. No OpenCode, checkout exato dos heads atuais e execução das suítes focadas descritas no runbook, sem Actions/CircleCI e sem credenciais.
2. Corrigir as 8 falhas de limpeza de arquivo temporário no Windows apenas se houver impacto funcional; não são falhas de contrato.
3. Implementar a extensão do pacote Gate V1 para consumir recibo ASVE e decisões versionadas, com testes de compatibilidade e rejeição fail-closed.
4. Fazer o Gate consumir o recibo de scoring diagnóstico sem transformar nota em aprovação; não definir limiar editorial sem decisão do proprietário.
5. Fechar as provas de concorrência e falha parcial do writer existente, incluindo tentativa de escrita REST fora da rota Gate.
6. Executar cenário integrado descartável: pauta → produção → revisão → ASVE → recibos → Gate → rascunho → readback, sem WordPress real.
7. Validar portabilidade Linux do Bot Redator quando houver ambiente, sem criar infraestrutura paga.

Nenhuma mudança de status será atribuída sem execução e evidência no SHA correspondente. Gate V2 permanece descontinuado.

## Execução estrutural final — 28/11/2026

### Gate V1 — SHA `3a74c28`

- `conexo-editorial-gate-core.php`: consumidor retrocompatível de sidecar ASVE no parecer privado; valida schema, hash canônico, `contract_sha256`, `run_id`, `article_sha256` e as flags de não autorização. Sidecars ausentes continuam válidos. Nenhum campo foi adicionado ao manifesto `cxeg-package:v1` e nenhum contrato v2 foi criado.
- Novos testes PHP isolados: `test_gate_v1_asve_sidecar.php` e `test_gate_v1_writer_isolado.php`. O writer cobre lock ocupado, nonce repetido, hash divergente, falha em `wp_insert_post`, falha em `update_post_meta`, estado parcial, readback divergente, limpeza de lock após sucesso e exceção.
- Verificação: 10 testes aprovados em checkout limpo clonado do GitHub; PHP lint 0 falhas. Inventário mantém 17 `MATCH`, 2 divergências documentadas, 1 credencial e 1 duplicata.

### MKT-RSS — SHA funcional `fceb66e`

- `editorial_gate_traceability.py`: `run_id` opcional, validado e vinculado ao digest do sidecar; ausência permanece retrocompatível.
- `wp_quality_executor.py`: passa `run_id` do evidence ou o fingerprint do parecer.
- `test_integrated_closure_20261128.py`: única matriz integrada, com produtor → revisão → scoring → ASVE → sidecar → validação → consumidor Gate → writer sintético → readback, incluindo contraprova de sidecar adulterado.
- Verificação focada: 43 aprovados, 1 ignorado, 20 subtests. Suíte completa no SHA final: 1544 aprovados, 1 ignorado, 72 subtests e as mesmas 8 falhas de limpeza de arquivo temporário no Windows.

### Limitações que permanecem

- Testes de writer usam stubs: não provam atomicidade de banco nem proteção contra bypass REST real.
- Consumo do sidecar ocorre pelo parecer privado, dentro de `cxeg-package:v1`; nenhum campo novo foi inserido no manifesto estrito.
- Não há WordPress efêmero, Linux, chave HMAC real nem aprovação humana. Produção, merge, deploy e ativação não foram executados.