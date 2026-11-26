# Orçamento e resiliência do provedor de IA (26/11/2026)

## Motivo

Durante a geração da pauta CT-021, a cadeia editorial recebeu HTTP 429 do Groq
mesmo sem uso anormal. A causa não foi cota diária: o plano gratuito limita
**8.000 tokens por minuto**. Redator + revisor + segunda tentativa rodavam em
segundos e estouravam essa janela.

Havia ainda dois problemas associados:

- `GROQ_MODEL` apontava para `llama-3.3-70b-versatile`, modelo fora do catálogo;
- `openai/gpt-oss-120b` rejeita `response_format=json_object` com HTTP 400.

## O que mudou

| Item | Antes | Depois |
|---|---|---|
| Controle de janela | nenhum | `provider_budget.ProviderBudget` com limite de 8.000 TPM e margem de 85% |
| Espaçamento | redator e revisor em segundos | chamadas grandes esperam a janela renovar (máx. 65 s por espera) |
| Modelo | falha se obsoleto | `modelo_disponivel()` consulta o catálogo e usa fallback gratuito |
| JSON forçado | 400 encerrava a geração | retry único sem `response_format`, com instrução de sistema preservada |
| Erro 429 | estourava toda a cadeia | código sanitizado, insumo preservado |
| Falha de provedor | pacote não era gerado | pacote offline pendente com `provider_failure` no manifesto |
| Log do SDK | `HTTP Request ... 429` no console | nível `httpx` elevado para `WARNING` |

## Regras preservadas

- Nenhuma falha de provedor vira `PASS`, aprovação humana ou autorização de publicação.
- Texto alterado invalida hash e recibo anteriores.
- O pacote gerado após falha permanece com `article_complete_for_human_review: false`,
  voz `NOT_APPLIED` e revisão assistida pendente.
- Nenhuma credencial, prompt ou corpo de resposta entra no manifesto público.

## Arquivos

- `mkt_flow_p0/provider_budget.py` — orçamento, fallback de modelo, chamada sanitizada.
- `mkt_flow_p0/rewriter.py` — redator usa o orçamento e o modelo resolvido.
- `mkt_flow_p0/editorial_development.py` — planejador e revisor usam a mesma ponte;
  falha do revisor não dispara um segundo ciclo caro.
- `pipeline_rss.py` — falha de provedor no `--import-article` gera pacote pendente.
- `mkt_flow_p0/editorial_import.py` — `provider_diagnostic` e `provider_failure` no resumo.

## Validação

- 131 testes direcionados aprovados (124 existentes + 7 novos).
- Sem mudança no Gate V1, sem merge, sem deploy e sem escrita em WordPress/Turso.
