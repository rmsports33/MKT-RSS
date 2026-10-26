# M05.5-F — Orçamento acumulado: protótipo isolado e restrições
Data 2026-10-26. PR #20. WordPress bloqueado.

## Feito
- CI anterior: 537 testes MKT-RSS e 52 do redator aprovados, run 40334776289; validação editorial run 40334777548 success.
- No modo CONEXO_CLOUD_PILOT=1, mkt_flow_p0/rewriter.py exige antes da chamada Groq um orçamento unitário explícito e reserva uma estimativa máxima num ledger SQLite, ou retorna erro.
- Ledger usa BEGIN IMMEDIATE e registro diário UTC, tentando evitar disputas entre processos no mesmo arquivo; não concede estorno em falhas, escolha conservadora.
- Variáveis adicionais obrigatórias: CONEXO_CLOUD_DAILY_BUDGET_USD e CONEXO_CLOUD_LEDGER_PATH (arquivo sob diretório existente).
- Novos testes cobrem esgotamento após múltiplas reservas, ausência de configuração, indisponibilidade de diretório e caminho positivo simulado.

## Limitação de segurança importante
O arquivo SQLite só agrega execução entre processos e runs que compartilhem a MESMA persistência real. O filesystem efêmero de cada runner GitHub Actions **não** é persistência compartilhada. Portanto, a configuração não deve ser declarada controle diário cloud global ou usada para liberar chamadas reais entre diferentes runners. Para operação segura, disponibilizar backend persistente central autorizado, com atualização atômica; ou limitar a exatamente um processo/execução e orçamento de execução verificável sem recorrência. Não utilizar um diretório local efêmero como ledger diário de produção. O uso de budget explícito não substitui aprovação financeira do usuário.

## Não executado / proibido
Credenciais Groq não verificadas; nenhuma chamada real, nenhuma mudança de secrets, nenhuma criação de agendador, merge, deploy ou WordPress. O fluxo factual pós-IA continua NAO_VERIFICADO.

## Gates
- Aguardar CI do commit mais recente.
- Revisar atomicidade e abrangência do ledger antes de considerar piloto externo.
- Obter aprovação de orçamento e backend persistente compartilhado adequado antes de Groq real.
