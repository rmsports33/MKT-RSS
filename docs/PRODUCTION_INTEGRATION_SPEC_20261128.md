# Especificação técnica das operações de integração — 28/11/2026

Documento de diagnóstico e preparação. Nenhuma operação de produção foi executada.

## 1. Separar os três artefatos do Gate V1

A integração atual possui três operações diferentes, que não podem ser tratadas como um único recibo:

1. **Parecer de qualidade** — `POST /conexo/v1/editorial/quality/record`. Registra o relatório privado e o fingerprint do snapshot. A leitura em `GET /conexo/v1/editorial/quality/{id}` retorna `post_id`, `valid_for_current_version` e `report`. Isso não é, por si só, um recibo HMAC de escrita.
2. **Aprovação humana** — `POST /conexo/v1/editorial/review/approve`. Registra decisão, identidade do revisor, hash da versão e referência editorial. Não publica.
3. **Envelope assinado de escrita** — `POST /conexo/v1/editorial/write`. O Gate decodifica `receipt` + `signature`, valida HMAC e o schema `conexo-editorial-write/1`, identidade, nonce, validade, intenção e `expected_sha256`; depois realiza a escrita protegida e readback.

O `wp_quality_executor.py` executa leitura, parecer e, com `--submit-quality`, grava o parecer privado. Ele **não gera nem submete** o envelope HMAC de escrita — essa separação é intencional e preservada. O envelope é produzido pelo caminho de publicação em `mkt_flow_p0/editorial_transport.py`, por meio de `core.prepare_write()`, com chave externa ao repositório e núcleo confiável verificado por `editorial_core.lock.json`. Tests com núcleo sintético confirmam o formato `receipt` + `signature`, nonce e readback; não provam chave de produção nem operação real. Portanto, não criar um segundo adaptador HMAC no executor de qualidade e não declarar que o recibo de qualidade equivale ao recibo assinado de escrita.

## 2. Estado real da proteção contra escrita concorrente

O candidato Gate V1 no PR #91 já contém parte importante do mecanismo:

- lock por post via opção `cxeg_lock_<post_id>` (ou nonce para criação);
- comparação do snapshot atual com `expected_sha256` antes da escrita;
- reserva/idempotência por nonce em `cxeg_op_<nonce>`;
- readback após `wp_insert_post` e comparação do hash do snapshot resultante.

Isso evita concorrência entre chamadas que usam a mesma rota do Gate para o mesmo post. **Não comprova atomicidade global**:

- a proteção precisa ser confrontada com todas as rotas REST e caminhos de escrita direta;
- o guard atual permite edição REST convencional de posts em rascunho/pending, portanto uma escrita externa pode não participar do lock do Gate;
- `wp_insert_post` e atualização de `_thumbnail_id` são operações separadas; falha parcial pode deixar alteração persistida e operação reservada para inspeção;
- a verificação final detecta divergência, mas não constitui rollback transacional.

Não criar uma segunda implementação chamada `commit_if_unchanged` antes de fechar essas lacunas. Primeiro consolidar a proteção existente, bloquear bypasses e provar o comportamento em testes concorrentes e de falha parcial. Só implementar mecanismo adicional se a prova demonstrar necessidade.

## 3. Integração ASVE / rastreabilidade com Gate

O PR #142 cria `editorial_gate_traceability.py` como sidecar encadeado. O próprio contrato e os testes declaram que o pacote atual `cxeg-package:v1` **não consome esse sidecar**.

Logo, a trilha ASVE está preparada e validável localmente, mas a integração com o Gate V1 ainda não está concluída. O fechamento deve reutilizar o envelope e a trilha canônica existentes, sem criar outro ledger:

- definir extensão compatível e versionada do pacote/envelope do Gate V1;
- incluir hashes do contrato, dossiê, revisão principal, recibo ASVE e decisões;
- fazer o Gate validar a integridade e a correspondência de versão desses dados;
- manter a ASVE como evidência editorial, nunca como aprovação humana nem autorização de publicação;
- preservar compatibilidade explícita com consumidores antigos ou rejeitar versões desconhecidas (fail-closed).

## 4. Integração do scoring 0–100

**Estado corrigido no head atual do PR #142:** `wp_quality_executor.py` já chama `editorial_quality_score.avaliar_artigo()` sobre o texto bruto efetivamente lido do WordPress e anexa o resultado a `report["quality_score_diagnostic"]`. O recibo contém o fingerprint do Revisor Único e o `content_sha256` do texto avaliado, repetido como `linked_content_sha256`. O parecer enviado à rota de qualidade do Gate transporta esse campo dentro do relatório.

A integração, portanto, está concluída no **produtor/executor e no transporte do parecer**. O que continua pendente é o **consumo semântico pelo Gate**: o Gate ainda não valida nem interpreta esse campo como evidência diagnóstica. Não há bloqueio, aprovação, publicação ou limiar baseado na nota.

O contrato canônico mantém escala `confirmed=false` e `publication_threshold=null`. Pesos e limiares não devem ser promovidos a política editorial obrigatória sem decisão do proprietário. A nota permanece exclusivamente diagnóstica e não substitui o Revisor Único, os 13 controles humanos nem a aprovação humana.

## 5. Sequência mínima de validação inteligente

Executar uma única matriz de testes de integração, em ambiente descartável e sem credenciais reais:

1. contrato/catálogo canônico ↔ cópia operacional;
2. MKT-RSS: Revisor Único + ASVE + scoring, incluindo hash e decisões P0/P1/P2;
3. pacote ASVE ↔ envelope Gate V1, incluindo rejeição de sidecar não reconhecido;
4. parecer de qualidade ↔ aprovação humana independente ↔ envelope HMAC;
5. Gate writer: dois escritores simultâneos para o mesmo post, nonce repetido, escrita REST direta concorrente, falha entre post e metadado, readback divergente e recuperação;
6. fluxo completo com WordPress efêmero: rascunho sintético, revisão, aprovação sintética de teste, escrita em rascunho e readback; nenhum post real.

Registrar SHA, ambiente, comandos, resultados e limites. Não usar GitHub Actions ou CircleCI como executor.

## 6. Limites de operação

- Sem escrita em WordPress ou Turso de produção.
- Sem publicação, aprovação ou agendamento reais.
- Sem ativação de plugin ou rotas.
- Sem provisionamento de chaves/opções/UUID.
- Sem segredo no repositório.
- Gate V2 permanece descontinuado e fora do escopo.
- Nenhuma evidência humana pode ser simulada por teste automatizado.

## Estado

**BLOCKED PARA HOMOLOGAÇÃO INTEGRADA.** A proteção de escrita, ASVE, scoring e Gate existem parcialmente, mas seus contratos e consumidores ainda não estão comprovados como um único fluxo.