# Consolidação factual — MKT-RSS — 18/11/2026

## Escopo e regra de leitura

Este documento consolida somente os fatos verificados nesta rodada sobre os PRs #124, #127 e #128. Não substitui recibos de execução nem declara homologação operacional. Estados de Hostinger, WordPress, Turso e cron que não foram lidos diretamente nesta rodada permanecem identificados como evidência reportada pelo operador/OpenCode.

**Regra de segurança:** não fazer merge, deploy, publicação, escrita em WordPress/Turso, alteração de cron ou limpeza de branches como consequência deste documento. Cada integração exige validação própria e revisão de risco.

## PR #127 — importação editorial, vídeo e proveniência

- PR: https://github.com/rmsports33/MKT-RSS/pull/127
- Branch: `fix/editorial-import-provenance-video-20261118`
- Base: `feat/hostinger-runtime-independente-20261113`
- Commit funcional validado pelo OpenCode: `6794c64da491bb863931057e6c968d70f7267fa4`.
- Commit `50d8435` adicionou somente o relatório de validação.
- Commits posteriores `740cdc8` e `f7ff6cf` alteraram a asserção do teste Android Drop para aceitar atributos na tag HTML `<table>` e mantiveram a verificação do cabeçalho `<th>Recurso</th>`.
- O estado atual reportado do PR nesta rodada: 10 commits, 11 arquivos, +1.400 / -17; permanece draft.

### Evidência e pendências

O OpenCode reportou, antes das duas últimas alterações de teste, 120 testes focados aprovados, 15 casos críticos aprovados e bateria ampla com 286 aprovados e 2 falhas. As mesmas duas falhas foram reportadas na baseline `3901ca0`, portanto não foram classificadas como regressões.

A correção da asserção Android Drop foi commitada em `f7ff6cf` e a correção da segunda falha foi localizada em `tests/test_imported_editorial_flow.py`, commitada em `198e1b3`. Ambas substituem a exigência literal de `<table>` por reconhecimento da tag com atributos, mantendo as verificações de conteúdo. **Nenhuma das duas correções foi executada em teste ainda.** Não atribuir PASS ao código posterior a `6794c64` sem nova execução.

A evidência anterior do OpenCode está no comentário https://github.com/rmsports33/MKT-RSS/pull/127#issuecomment-6985765535. O relatório original está em https://github.com/rmsports33/MKT-RSS/blob/50d84358bb9a5434b03a031e86226ee199e890b7/docs/VALIDACAO_PR127_20261118.md.

### Próxima ação segura

Executar no checkout isolado do OpenCode os dois testes afetados e os quatro módulos focados; registrar SHA exato, comando, ambiente, resultado e diferenças. O comentário de execução está no PR #127. Não executar no checkout operacional Hostinger e não acessar serviços reais. Se a segunda asserção exigir mudança, ajustar apenas o teste para reconhecer o HTML semanticamente produzido, preservando as verificações de conteúdo e segurança.

## PR #124 — fila de correção do Gate

- PR: https://github.com/rmsports33/MKT-RSS/pull/124
- Branch divergente: `feat/gate-correction-queue-20261117`
- HEAD registrado: `23180510b4ff5c4e9dd1aed08966a4c0ee2afc44`.
- Divergência registrada na comparação anterior: 14 commits à frente e 29 atrás da base.
- PR permanece draft e não deve ser integrado ou rebaseado.

Os arquivos `mkt_flow_p0/editorial_correction_queue.py` e `tests/test_editorial_correction_queue.py` são redundantes em relação à linha operacional posterior: a normalização de `title.rendered` / `title.raw` e os testes correspondentes já chegaram à base por trabalho posterior (PR #125). A reconciliação isolada apontou que portar a versão antiga removeria a normalização e cinco testes. Não portar esses dois arquivos.

Os documentos originais do PR #124 são fotografias históricas:
- `FASE1_DIAGNOSTICO_20261117.md`: contém instruções de SSH obsoletas após registrar que o JS real foi reconciliado no repositório pelo PR #78. A seção de próximos passos deve ser considerada superada; não executar os comandos antigos.
- `MATRIZ_UNICA_PENDENCIAS_20261116.md`: inventário de 16/11, com status e sequência anteriores a decisões e entregas posteriores. Não é matriz atual.
- `STATUS_FRONTENDS_20261116.md`: fotografia de 16/11, não é status operacional atual.

Preservar os três arquivos como histórico. Não os copiar para a linha operacional como documentação vigente. Atualizações futuras devem partir de evidências recentes e registrar a data de cada leitura.

## PR #128 — política de consolidação

- PR: https://github.com/rmsports33/MKT-RSS/pull/128
- Branch: `docs/consolidacao-continua-mkt-rss-20261118`
- Commits existentes: `a367856` (política) e `5795e35` (AGENTS.md).
- Escopo documental; permanece draft.
- Esta consolidação é acrescentada ao mesmo PR para manter política e estado factual próximos, sem tocar runtime.

## Evidência operacional externa

Os relatos anteriores do OpenCode indicam que o checkout operacional `~/mkt-rss-runner` permaneceu na branch `feat/hostinger-runtime-independente-20261113`, HEAD `3901ca0`, com alterações locais e arquivos não rastreados preservados. Essa informação não foi verificada por SSH nesta rodada; portanto, deve continuar classificada como evidência reportada, não como inspeção independente.

Não há autorização para limpar arquivos não rastreados, trocar de branch, fazer reset, copiar código para o checkout operacional ou executar escrita remota.

## Critério de encerramento desta frente

Esta frente só poderá ser considerada concluída quando:
1. os testes afetados forem executados no checkout isolado e os resultados forem registrados para o SHA final;
2. a segunda falha histórica for resolvida ou formalmente mantida como falha preexistente, com evidência comparativa reproduzível;
3. a descrição e o relatório do PR #127 corresponderem ao SHA efetivamente testado;
4. os PRs permanecerem sem integração até revisão explícita e segura;
5. nenhuma alteração operacional não autorizada ocorrer.

**Estado em 18/11/2026:** documentação e descrições reconciliadas; as duas asserções históricas foram corrigidas; execução final dos testes pendente no OpenCode. Nenhuma integração ou alteração de produção realizada.
