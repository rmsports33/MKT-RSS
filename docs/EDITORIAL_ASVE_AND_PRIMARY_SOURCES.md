# Fontes de Origem e Análise Secundária de Valor Editorial (ASVE)

**Contrato canônico:** Conexo OS v1.1 · SHA-256 `8d59e75e4fb03b899ceee73051d7a19794da2ff9b91b2870d4907a7b7c5b30b8`.

## Arquitetura preservada

O MKT-RSS mantém o produtor editorial, o Revisor Único, o Gate e o mecanismo de handoff existentes. Esta implementação acrescenta uma modalidade ao revisor existente e amplia a trilha de evidências; não cria outro agente, revisor, publicador, serviço de IA, chave ou cron.

## Catálogo de fontes de origem

`data/editorial-primary-source-registry-v1.json` contém 18 pontos de entrada:
- Brasil: EPE, ONS, ANEEL, CCEE, Anatel, MCom, IBGE, Portal da Legislação/Planalto, Diário Oficial da União e Fala.BR (canal para solicitações LAI).
- Internacional: IEA, Ember, EIA e Eurostat.
- Descoberta científica: Crossref e OpenAlex.
- Tecnologia, segurança e mercado: NIST NVD e SEC EDGAR.

O catálogo é uma lista de descoberta, não uma whitelist de verdade. A correspondência de host sugere instituição e papel provável, mas sempre retorna `NAO_VERIFICADA`. Domínio `.gov`, `.edu`, DOI, PDF, HTTPS ou nome conhecido não comprovam uma afirmação.

Para legislação e decisões, abrir o texto original, edição do Diário Oficial e eventuais retificações. Quando a informação não estiver publicada, Fala.BR pode ser utilizado para solicitar documentos e séries sob a LAI. A resposta obtida precisa ser preservada com protocolo, data, anexos e limites de acesso; o canal de pedidos não é fonte factual em si.

A lista legada `mkt_flow_p0/fontes_primarias.json` permanece específica para a seleção de fabricantes/fornecedores. Ela não deve ser usada como catálogo universal nem misturada ao classificador geral.

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
- **P1:** melhoria material. Exige decisão editorial registrada para a versão exata. Aceitar/rejeitar/transferir para pauta exige justificativa.
- **P2:** pauta futura separada, não bloqueia o artigo atual.

Cada apontamento exige localização, observação, impacto para o leitor, evidências/claims existentes, ação recomendada, IDs de páginas internas publicadas quando aplicável e, para P2, título, justificativa e pergunta de pesquisa. O validador rejeita IDs inventados, páginas não publicadas, respostas que tentem reescrever o texto, campos extras e versões divergentes. Zero achados é um resultado válido.

## Integração no Revisor Único e no executor

- `incorporar_analise_secundaria(...)` preserva o parecer principal e acopla o recibo; nunca autoriza publicação.
- `executar_revisao_com_asve(...)` orquestra a chamada independente e a integração.
- `analisar_com_provedor_editorial_existente(prompt)` usa o cliente Groq já presente no projeto e o mesmo `provider_budget.BUDGET`. A chamada é opt-in; não cria provedor, conta, chave nem orçamento separado.
- O executor privado `mkt_flow_p0.wp_quality_executor` aceita `--secondary-analysis`. Sem a flag, o fluxo anterior não muda. Com a flag, usa o corpo bruto do post em rascunho, o dossiê `asve_dossier` fornecido no arquivo de evidências e consulta até 75 posts publicados via REST somente leitura. O recibo é vinculado ao conteúdo examinado e guardado no relatório privado.
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

### Registro de P2 no backlog existente

Os achados P2 são encaminhados para `mkt_flow_p0.fila_pautas.registrar_topico_asve`, somente depois de a releitura do WordPress confirmar o mesmo fingerprint do rascunho, usando o mesmo armazenamento SQLite/Turso da fila editorial atual. A chave idempotente combina ID do artigo, hash da versão e ID do achado. Não cria um URL falso, RSS artificial, tabela de pauta duplicada ou nova fila. O status inicial é `DESCOBERTA`; o tema não é automaticamente selecionado ou produzido.

## Controle de custos

O adaptador utiliza o cliente e orçamento compartilhados já disponíveis. A chamada adicional só ocorre quando a ASVE é explicitamente solicitada por código/orquestrador ou pela flag `--secondary-analysis`. O modo offline continua sem chamada de modelo. Nenhum plano pago, API key ou serviço externo novo foi adicionado.

## Testes adicionados

- `tests/test_editorial_secondary_analysis.py`: hash, limites, P0/P1/P2, dossiê completo, referências válidas, rejeição de reescrita, decisões e versionamento.
- `tests/test_primary_source_registry.py`: catálogo, papel consultivo, TLD desconhecido, HTTPS e validação de claims.
- `tests/test_editorial_secondary_reviewer_integration.py`: fluxo combinado, decisões e persistência P2.
- `tests/test_wp_quality_executor.py`: flag opt-in, recibo, páginas publicadas e uso de cliente simulado.
- `tests/test_fila_pautas.py`: idempotência do backlog e ausência de escrita WordPress.

Foram adicionados 33 casos focados: 13 para ASVE, 7 para o catálogo de fontes, 5 para a integração do Revisor Único, 5 para o executor WordPress e 3 para o backlog P2. **A execução destes testes ainda está pendente** porque esta sessão não tem checkout local do repositório e o projeto evita disparar GitHub Actions para testes rotineiros. Não declarar PASS até rodar a suíte focada e a suíte de regressão no ambiente de desenvolvimento.

## Homologação editorial

Depois dos testes locais, executar um piloto sem publicação com três a cinco artigos de gêneros diferentes. Comparar os achados ASVE com avaliação humana independente e medir: utilidade, falsos positivos, decisões aceitas/rejeitadas, esforço editorial e temas P2 realmente aproveitados. Só declarar homologação de qualidade depois de um piloto cego com pelo menos três gêneros. Gate e aprovação humana continuam separados.
