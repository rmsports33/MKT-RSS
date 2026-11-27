# Fontes de Origem e Análise Secundária de Valor Editorial (ASVE)

**Contrato:** Conexo OS v1.1 · SHA-256 `966310987434eefb48ac6358fdb3eb01ade22ef37634902752ef081215dba701`.

## Arquitetura existente preservada

O MKT-RSS já dispõe de pesquisa complementar, pacote de handoff, contrato estruturado de evidências e `mkt_flow_p0.revisor_qualidade_unico`. Esta entrega acrescenta:
- catálogo versionado e classificador consultivo de fontes;
- metadados mínimos por afirmação/fonte;
- uma segunda modalidade de análise, sem criar um segundo agente de revisão;
- validação de IDs, limite de cinco achados, prioridades, hash de versão e decisões.

`fontes_primarias.json` permanece como lista positiva legada para o fluxo de fabricantes/produtos. O novo `data/editorial-primary-source-registry-v1.json` é um catálogo transversal de descoberta. Não substituir um pelo outro nem tratar catálogo, domínio ou TLD como prova factual.

## Fonte de origem: usar corretamente

`mkt_flow_p0.primary_source_registry.classify_source_url(url)` retorna uma sugestão de origem e um estado inicial `NAO_VERIFICADA`. A função:
- aceita somente HTTPS sem userinfo e portas não padrão;
- identifica correspondência exata ou subdomínio de uma instituição cadastrada;
- nunca marca um fato como confirmado;
- classifica domínios desconhecidos como `discovery_lead`, mesmo quando usam TLD institucional.

`validate_source_record` confere se o registro documenta URL, responsável, tipo, papel, data de publicação, período de referência, localização na fonte, metodologia, limitações e data de consulta. `validate_claim_record` verifica a estrutura e os IDs referenciados, mas retorna explicitamente `factuality_verified=false` e `semantic_support_verified=false`.

Exemplo de dossiê:

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

Não copiar esse exemplo como dado real sem preencher os identificadores, datas, página e metodologia efetivamente verificados. Campos ausentes devem ser `not_provided` ou `not_applicable`, nunca inferidos.

## ASVE: segunda leitura, não reescrita

Módulo: `mkt_flow_p0/editorial_secondary_analysis.py`.

Integração proposta com o Revisor Único existente:
1. Executar a revisão principal normalmente.
2. Construir uma entrada ASVE independente com o artigo, dossiê e páginas internas publicadas. Não transmitir o parecer principal nem feedback de reescrita.
3. O orquestrador existente chama o analisador/modelo que já estiver disponível e autorizado, usando `build_analysis_request(...)` e `run_secondary_analysis(..., analyzer)`. Não é criado serviço, chave, cron ou provedor novo.
4. Validar o retorno por `validate_analysis_result`.
5. Anexar ao recibo do Revisor Único com `attach_to_unique_reviewer`. A função preserva o veredito principal, não escreve no WordPress e mantém autorização de publicação falsa.
6. Depois da decisão editorial, registrar as disposições com `validate_dispositions`, sempre vinculadas ao hash do artigo.

A modalidade cobre contexto global, conexões relevantes, contrapontos/limitações, valor original para o leitor e continuidade editorial. Aceita de zero a cinco apontamentos. P0 exige incorporação para fechar; P1 requer decisão e justificativa quando não incorporado; P2 é pauta futura e não bloqueia o artigo atual.

Cada apontamento inclui localização, observação, impacto para o leitor, referências a fontes/claims existentes, ação recomendada, referências somente a páginas publicadas do ConexoTech e, quando P2, uma pauta futura estruturada.

## Limites de segurança

- Sem reescrita, parágrafos substitutos ou comentários cosméticos.
- Sem URLs de evidência ou páginas internas inventadas.
- Sem análise apresentada como prova factual.
- Sem alteração do corpo, metadados ou status de WordPress.
- Sem autorização, aprovação ou publicação.
- O hash do artigo precisa corresponder exatamente à versão analisada.
- Um resultado com zero achados é válido e não deve ser penalizado.
- Uma segunda passada pontual verifica apenas as decisões aplicadas; não reabre análise ampla sem mudança material.

## Custos e execução

O módulo não acessa rede e não chama modelo por conta própria. O analisador é injetado pelo orquestrador. Assim, a ASVE pode usar o provedor e a cota já disponíveis; não gera nova despesa automaticamente. O pipeline RSS não executará uma segunda chamada de IA por padrão.

## Testes

- `tests/test_editorial_secondary_analysis.py`: contratos, hash, limites, P0/P1/P2, links internos publicados, rejeição de reescrita, decisões e preservação do veredito.
- `tests/test_primary_source_registry.py`: catálogo, domínio conhecido como pista, TLD desconhecido sem confiança automática, HTTPS e estrutura de claims.

Foram adicionados 23 casos de teste focados (13 ASVE, 7 catálogo de fontes, 3 integração com Revisor Único). **A execução dos novos testes ainda não foi efetuada neste ambiente**; não declarar PASS até executar no checkout integral. A suíte anterior de PR #142 não substitui os novos testes nem uma homologação do fluxo de IA.

## Homologação futura

Executar offline no checkout integral, depois o piloto ASVE em três a cinco artigos de gêneros diferentes, sem publicação. Comparar achados com avaliação humana independente e medir utilidade, falsos positivos, esforço de decisão e taxa de apontamentos rejeitados. Só declarar qualidade homologada após piloto cego em pelo menos três gêneros. O Gate e a decisão humana de publicação permanecem intactos.
