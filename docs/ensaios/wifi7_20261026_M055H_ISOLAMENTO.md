# M05.5-H — Resultado e limites do isolamento remoto
Data: 2026-10-26. PR #20 (draft). Nenhuma autorização de merge, deploy, IA paga ou WordPress.

## Inspeção e correção
- CI run 40336497871 anterior: 552 passed, 6 failed. Cinco falhas derivavam de sequência literal de barra+n na linha do ledger em `mkt_flow_p0/cloud_budget_ledger.py`, deixando `limite` não definido. Uma contraprova de preço/data falhou devido ao regex de separação de frases com escape dobrado.
- Corrigidos os dois arquivos em commits ed65314221cf9a2a9f64eabdb6a1cec02b123f48 e b8b561664dd625798b5438dd3943d9d92fc22a6d.
- Testes remotos posteriores precisam ser consultados por SHA; não inferir aprovação antes de conclusão.

## Isolamento: escopo realmente disponível
- O executor experimental ainda aceita um callback Python arbitrário. Remover variáveis WordPress ou gravar `escreveu=False` **não é isolamento**. A função poderia usar rede, arquivos ou herdar permissões da execução.
- GitHub Actions com `contents: read` é útil para testes de código, mas **não** é garantia de egress negado e não deve receber secrets de WP, IA ou tokens de escrita para este ensaio.
- A reserva SQLite em filesystem efêmero de GitHub Actions não controla gastos acumulados entre execuções. O ledger deve negar chamadas reais nesse ambiente até haver um controle central persistente ou um orçamento estritamente administrado em provedor.
- Sem ambiente remoto de rede restrita comprovada, não conectar adaptador de IA real. Antes, exigir um processo/container com credenciais somente de leitura, políticas de egress explícitas, contador central de orçamento e teste de tentativa de rede proibida que falhe fechado.

## Factualidade
`check_rendered` oferece inspeção complementar pós-HTML; não está ligado ao renderizador de produção nem prova factualidade semântica. O cruzamento preço/data por mesma frase não vincula necessariamente produto, preço, loja, data e URL. Manter revisão obrigatória.

## Gates preservados
Verificacao factual: NAO_VERIFICADO. WordPress: bloqueado. PR Draft. Sem merge/deploy/publicação/chamada LLM.
