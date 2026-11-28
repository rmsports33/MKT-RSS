# Fontes de Origem e Análise Secundária de Valor Editorial (ASVE)

**Contrato canônico:** Conexo OS v1.1 · SHA-256 `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

## Arquitetura preservada

O MKT-RSS mantém o produtor editorial, o Revisor Único, o Gate e o mecanismo de handoff existentes. Esta implementação acrescenta uma modalidade ao revisor existente e amplia a trilha de evidências; não cria outro agente, revisor, publicador, serviço de IA, chave ou cron.

## Catálogo de fontes de origem

`data/editorial-primary-source-registry-v1.json` contém 21 pontos de entrada:
- Brasil: EPE, ONS, ANEEL, CCEE, Anatel, MCom, IBGE, Portal da Legislação/Planalto, Diário Oficial da União e Fala.BR (canal para solicitações LAI).
- Internacional: IEA, Ember, EIA, Eurostat, ITU, World Bank e OECD.
- Descoberta científica: Crossref e OpenAlex.
- Tecnologia, segurança e mercado: NIST NVD e SEC EDGAR.

O catálogo é uma lista de descoberta, não uma whitelist de verdade. A correspondência de host sugere instituição e papel provável, mas sempre retorna `NAO_VERIFICADA`. Domínio `.gov`, `.edu`, DOI, PDF, HTTPS ou nome conhecido não comprovam uma afirmação.

Para legislação e decisões, abrir o texto original, edição do Diário Oficial e eventuais retificações. Quando a informação não estiver publicada, Fala.BR pode ser utilizado para solicitar documentos e séries sob a LAI. A resposta obtida precisa ser preservada com protocolo, data, anexos e limites de acesso; o canal de pedidos não é fonte factual em si.

A lista legada `mkt_flow_p0/fontes_primarias.json` permanece específica para a seleção de fabricantes/fornecedores. Ela não deve ser usada como catálogo universal nem misturada ao classificador geral.

## Duas trilhas distintas: descoberta editorial e evidência primária

O projeto mantém duas trilhas que não devem ser confundidas:

1. **Descoberta de pauta (RSS e imprensa):** `mkt_flow_p0/rss_ingestor.py` e
   `research_candidates.py` coletam manchetes e resumos de feeds editoriais já
   configurados. O material é rotulado como pista/RSS pendente de apuração; serve
   para descobrir acontecimentos, encontrar termos e direcionar a pesquisa.
   Não confirma fatos, não equivale a corroboração independente e não pode
   alimentar automaticamente uma claim como `CONFIRMADA`.
2. **Apuração de origem (documentos, bases e APIs):** o catálogo
   `data/editorial-primary-source-registry-v1.json` orienta a busca direta de
   datasets, documentos originais, registros legais, estudos e APIs de quem
   produziu a informação. A fonte concreta e seu locator são registrados por
   afirmação no dossiê.

As listas RSS existentes são majoritariamente fontes jornalísticas de
tecnologia, não um monitor completo de órgãos primários. Nenhum URL de feed
oficial deve ser inventado nem tratado como oficial só porque foi publicado
por um agregador. Quando um órgão não oferece feed oficial verificável, usar
seu catálogo oficial de publicações, API, página de dados abertos ou boletim
institucional; registrar data da consulta e versão do documento. O monitor de
RSS atual continua sendo uma camada de descoberta, não uma automação de
apuração nem um novo cron.

**Exemplo recente de uso correto:** a pauta de data centers foi aprofundada
diretamente com o PDE 2036 e seu Caderno de Demanda da EPE, e com a Lei
15.504/2026 no Portal da Legislação. Esses documentos foram adicionados às
URLs do registro EPE/Planalto sem criar registros ou serviços paralelos. Uma
taxa de 13,7% publicada pela EPE não foi combinada automaticamente com a série
3→30 TWh; a discrepância aritmética aparente foi registrada para esclarecimento
da origem, base e escopo.

## Classificação por afirmação

O papel de uma fonte é relativo à afirmação:
- `primary_origin`: entidade que produziu a informação ou o documento original.
- `independent_measurement`: medição ou verificação independente.
- `secondary_analysis`: análise de terceiros a partir de fontes/dados.
- `interested_party_statement`: declaração de parte interessada.
- `discovery_lead`: pista de pesquisa ainda não validada.

Estados: `CONFIRMADA`, `CORROBORADA`, `ATRIBUIDA`, `PROJETADA` e `NAO_VERIFICADA`.

`mkt_flow_p0.primary_source_registry` oferece:
- `load_registry()`: validar a estrutura do catálogo e IDs.
- `classify_source_url(url)`: classificar uma URL como pista, nunca como fato validado.
- `validate_source_record(source)`: exigir URL, responsável, tipo, papel, data publicada, período de referência, localização exata, metodologia, limitações e data de consulta.
- `validate_claim_record(claim, sources)`: conferir estrutura e referências; retorna explicitamente `factuality_verified=false` e `semantic_support_verified=false`.

O dossiê ASVE também aplica esses validadores antes de enviar o material ao modelo. Projeções, estimativas, declarações e medições permanecem distintas. Fontes que apenas reproduzem o mesmo release não contam como corroboração independente. A apuração procura evidências contrárias e hipóteses alternativas.

## Análise Secundária de Valor Editorial

Módulo: `mkt_flow_p0/editorial_secondary_analysis.py`.

A ASVE é uma segunda leitura independente, com contexto separado da revisão principal. Recebe o texto exato e seu SHA-256, o dossiê estruturado e um catálogo de páginas internas. O prompt não recebe o parecer da revisão principal e trata artigo/documentos/claims/páginas como dados não confiáveis, ignorando eventuais instruções embutidas.

Dimensões:
1. contexto global;
2. conexões relevantes e temas adjacentes;
3. contrapontos e limitações;
4. valor original para o leitor;
5. continuidade editorial.

O retorno aceita de zero a cinco apontamentos:
- **P0:** falha material factual/metodológica/editorial. Mantém `REVISAO_NECESSARIA`; corrigir e fazer nova análise vinculada ao novo hash.
- **P1:** melhoria material. Exige decisão editorial registrada para a versão exata: incorporar ou aceitar/rejeitar com justificativa. P1 não pode ser silenciosamente rebaixado para pauta futura; aprofundamentos separados são P2.
- **P2:** pauta futura separada, não bloqueia o artigo atual.

Cada apontamento exige localização, observação, impacto para o leitor, evidências/claims existentes, ação recomendada, IDs de páginas internas publicadas quando aplicável e, para P2, título, justificativa e pergunta de pesquisa. O validador rejeita IDs inventados, páginas não publicadas, respostas que tentem reescrever o texto, campos extras e versões divergentes. Zero achados é um resultado válido.

## Integração no Revisor Único e no executor

- `incorporar_analise_secundaria(...)` preserva o parecer principal e acopla o recibo; nunca autoriza publicação.
- `executar_revisao_com_asve(...)` orquestra a chamada independente e a integração.
- `analisar_com_provedor_editorial_existente(prompt)` usa o cliente Groq já presente no projeto e o mesmo `provider_budget.BUDGET`. A chamada é opt-in; não cria provedor, conta, chave nem orçamento separado.
- O executor privado `mkt_flow_p0.wp_quality_executor` aceita `--secondary-analysis`. Sem a flag, o fluxo anterior não muda. Com a flag, usa o corpo bruto do post em rascunho, o dossiê `asve_dossier` fornecido no arquivo de evidências e consulta posts e páginas publicados, paginados até 500 por tipo via REST somente leitura. O recibo é vinculado ao conteúdo examinado e guardado no relatório privado.
- O executor relê o post e verifica o fingerprint depois da análise; se o rascunho mudou, falha e exige nova execução.
- Nenhuma operação da ASVE altera corpo, metadados, status ou publicação do WordPress. A opção anterior `--submit-quality` é separada e não publica o artigo; deve continuar sujeita às salvaguardas do Gate.

### Exemplo de dossiê mínimo (estrutura ilustrativa)

```json
{
  "sources": [{
    "source_id": "epe-pde-2036",
    "url": "https://www.epe.gov.br/...",
    "publisher": "Empresa de Pesquisa Energética",
    "source_type": "planning_document",
    "source_role": "primary_origin",
    "published_at": "2026-...",
    "reference_period": "2026-2036",
    "locator": "Caderno de Demanda, tabela/seção identificada",
    "methodology": "Cenário e premissas descritos no documento",
    "limitations": "Projeção condicionada a premissas, não medição",
    "retrieved_at": "2026-..."
  }],
  "claims": [{
    "claim_id": "claim-data-centers-demand",
    "claim_text": "A projeção indica aumento do consumo...",
    "source_ids": ["epe-pde-2036"],
    "source_role": "primary_origin",
    "verification_status": "PROJETADA"
  }]
}
```

O exemplo não representa uma afirmação verificada. Antes do uso real, substituir reticências por URL, documento, datas, localização, metodologia e limitações efetivamente conferidas.

### Relação com o avaliador de qualidade 0–100

O score é diagnóstico e não certifica a origem nem o suporte semântico das
afirmações. Em especial:

- quantidade de links internos não é quota nem gatilho automático: zero,
  um ou vários links não geram bloqueio ou penalidade por contagem; quando
  houver links, existência do destino, publicação, âncora e pertinência
  contextual ficam para revisão humana;
- o mapa de raciocínio Canaltech é referência de comparação/review e não deve
  penalizar notícia, análise, guia ou nota breve;
- a presença de palavras como “Brasil” ou de um domínio `.gov.br`/`.com.br`
  não comprova que uma fonte sustenta uma claim. O score sinaliza necessidade
  de revisão por claim, sem emitir PASS factual ou bloquear por heurística lexical.

Essas regras preservam a separação entre detecção automática, dossiê de
evidências, julgamento editorial e autorização do Gate.

## Registro de P2 no backlog existente

Os achados P2 são encaminhados para `mkt_flow_p0.fila_pautas.registrar_topico_asve`, somente quando `--register-asve-topics` for explicitamente informado e depois de a releitura do WordPress confirmar o mesmo fingerprint do rascunho, usando o mesmo armazenamento SQLite/Turso da fila editorial atual. Sem essa segunda flag, o P2 permanece apenas no recibo ASVE e nenhuma gravação na fila compartilhada ocorre. A chave idempotente combina ID do artigo, hash da versão e ID do achado. Não cria um URL falso, RSS artificial, tabela de pauta duplicada ou nova fila. O status inicial é `DESCOBERTA`; o tema não é automaticamente selecionado ou produzido.


## Sidecar de rastreabilidade para o Gate

Módulo: `mkt_flow_p0.editorial_gate_traceability`.

A implementação atual do Gate RC10.5 valida `cxeg-package:v1` com manifesto de seis campos e rejeita campos adicionais. Não inserir ASVE, claims ou metadados extras dentro desse manifesto: isso quebraria a compatibilidade do contrato estrito existente.

Para preservar a rastreabilidade sem alterar o Gate ativo:
- o Revisor Único gera um sidecar independente `conexo-editorial-gate-traceability-sidecar/1`, vinculado ao SHA-256 do artigo, do contrato canônico, do dossiê de evidências, da revisão principal, do recibo ASVE e das decisões;
- o sidecar lista IDs de fontes e claims, estados de verificação, IDs P0/P1/P2 e o estado do handoff;
- o hash do sidecar permite detectar alterações posteriores, mas não é assinatura digital nem comprovação factual;
- P0 exige nova versão do artigo; P1 exige decisão vinculada ao hash; P2 não bloqueia;
- o executor pode exportar o sidecar por `--gate-traceability-output-file` (arquivo privado, sem sobrescrita).

**Compatibilidade explícita:** o Gate atual `cxeg-package:v1` não consome nem valida o sidecar. O resultado `TRACEABILITY_COMPLETE_FOR_GATE_CONSUMER` significa que a trilha editorial está estruturalmente completa para um consumidor futuro; não significa Gate aprovado, publicação autorizada ou aprovação humana. A incorporação ao Gate exige uma evolução versionada do contrato e testes no harness RC10.5 isolado, sem adicionar campos ao manifesto v1 e sem tocar o plugin ativo.

## Controle de custos

O adaptador utiliza o cliente e orçamento compartilhados já disponíveis. A chamada adicional só ocorre quando a ASVE é explicitamente solicitada por código/orquestrador ou pela flag `--secondary-analysis`. O modo offline continua sem chamada de modelo. Nenhum plano pago, API key ou serviço externo novo foi adicionado.

## Testes adicionados

- `tests/test_editorial_secondary_analysis.py`: hash, limites, P0/P1/P2, dossiê completo, referências válidas, rejeição de reescrita, decisões e versionamento.
- `tests/test_primary_source_registry.py`: catálogo, papel consultivo, TLD desconhecido, HTTPS e validação de claims.
- `tests/test_editorial_secondary_reviewer_integration.py`: fluxo combinado, decisões e persistência P2.
- `tests/test_wp_quality_executor.py`: flag opt-in, recibo, páginas publicadas e uso de cliente simulado.
- `tests/test_fila_pautas.py`: idempotência do backlog e ausência de escrita WordPress.

Foram adicionados 46 casos focados: 14 para ASVE, 7 para o catálogo de fontes, 6 para a integração do Revisor Único, 8 para o executor WordPress, 3 para o backlog P2 e 8 para o sidecar de rastreabilidade do Gate. **A execução destes testes ainda está pendente** porque esta sessão não tem checkout local do repositório e o projeto evita disparar GitHub Actions para testes rotineiros. Não declarar PASS até rodar a suíte focada e a suíte de regressão no ambiente de desenvolvimento.

## Homologação editorial

Depois dos testes locais, executar um piloto sem publicação com três a cinco artigos de gêneros diferentes. Comparar os achados ASVE com avaliação humana independente e medir: utilidade, falsos positivos, decisões aceitas/rejeitadas, esforço editorial e temas P2 realmente aproveitados. Só declarar homologação de qualidade depois de um piloto cego com pelo menos três gêneros. Gate e aprovação humana continuam separados.

### Regressões adicionais do avaliador de qualidade

Foram acrescentados cinco testes em `tests/test_editorial_quality_score.py` para
assegurar que o mapa de raciocínio seja aplicado somente a gêneros compatíveis,
que links acima da recomendação não se tornem bloqueio e que uma URL de domínio
brasileiro não valide automaticamente afirmações sobre o Brasil. Esses testes
estão adicionados ao PR, mas ainda não foram executados nesta sessão.
