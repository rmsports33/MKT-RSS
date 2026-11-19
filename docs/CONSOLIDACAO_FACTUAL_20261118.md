# Consolidação factual — MKT-RSS — 19/11/2026

## Escopo e regra de leitura

Este documento consolida somente os fatos verificados nesta rodada sobre os PRs #124, #127 e #128. Não substitui recibos de execução nem declara homologação operacional. Estados de Hostinger, WordPress, Turso e cron que não foram lidos diretamente nesta rodada permanecem identificados como evidência reportada pelo operador/OpenCode.

**Regra de segurança:** não fazer merge, deploy, publicação, escrita em WordPress/Turso, alteração de cron ou limpeza de branches como consequência deste documento. Cada integração exige validação própria e revisão de risco.

## PR #127 — importação editorial, vídeo e proveniência

- PR: https://github.com/rmsports33/MKT-RSS/pull/127
- Branch: `fix/editorial-import-provenance-video-20261118`
- Base: `feat/hostinger-runtime-independente-20261113`
- HEAD atual confirmado pelo GitHub em 19/11/2026: `854feb33dd94003df8d768cc52edeb1366b4c504`.
- Base permanece `feat/hostinger-runtime-independente-20261113` (`3901ca0802d500381d7b0372b4d75dc6fc2ec40e`).
- 23 arquivos alterados; PR permanece draft e não mesclado.
- Os commits de correção das asserções HTML estão incluídos no HEAD atual, mas não foram executados em teste após essas alterações.

### Evidência e pendências

O OpenCode reportou, antes das duas últimas alterações de teste, 120 testes focados aprovados, 15 casos críticos aprovados e bateria ampla com 286 aprovados e 2 falhas. As mesmas duas falhas foram reportadas na baseline `3901ca0`, portanto não foram classificadas como regressões.

A correção da asserção Android Drop foi commitada em `f7ff6cf` e a correção da segunda falha foi localizada em `tests/test_imported_editorial_flow.py`, commitada em `198e1b3`. Ambas substituem a exigência literal de `<table>` por reconhecimento da tag com atributos, mantendo as verificações de conteúdo. **Nenhuma das duas correções foi executada em teste no HEAD atual `854feb33`.** Não atribuir PASS ao código posterior a esse SHA sem nova execução.

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

## Reconciliação WordPress autenticada — 19/11/2026

A leitura WordPress autenticada de `draft/pending` encontrou 150 itens atuais (100 + 50), não 149 como na fotografia de 13/11. Os 150 foram consultados individualmente em `context=edit` para verificar corpo, excerpt, mídia e categorias.

- 23 sem `featured_media`.
- 10 sem categoria ou na categoria padrão `Uncategorized` (ID 1).
- 137 sem excerpt; 13 com excerpt preenchido. A listagem resumida do conector não refletia corretamente o excerpt, por isso a contagem usa leituras individuais.
- Conteúdo extremamente curto: #9124 (534 caracteres), #9115 (392), #9117 (399) e #9122 (541).
- #9633 é teste explícito `[TESTE NAO PUBLICAR]`; deve permanecer excluído de fluxo publicável.
- #9906 e #9900 têm corpo com cerca de 6 mil caracteres e excerpt, mas sem mídia destacada e categoria padrão.
- Nenhum post foi editado, excluído, restaurado, agendado ou publicado.

A leitura de plugins WordPress também atualizou o estado: Gate controlado RC10.4 ativo; Native SEO controlado 0.5.2 ativo; Rank Math 1.0.280 ativo; Gate 0.3.3 inativo. O estado ativo do plugin não comprova emissão Native SEO pública nem homologação RC10.5.

Readback do post temporário #9907 em contextos `edit` e `view` confirmou conservação do conteúdo/iframe/VideoObject e correlação de ID/status/modified, mas o conector achatou `content` em string. Isso não comprova o envelope REST nativo `content.raw` / `content.rendered`; o contrato estrito do adaptador continua bloqueando corretamente. O post permanece na lixeira.

Comentários com evidências atuais foram registrados nas issues MKT-RSS #111 e #114 e no PR #127.

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

**Estado em 19/11/2026:** documentação atualizada para o HEAD `854feb33`; reconciliação WordPress somente leitura concluída; readback nativo ainda pendente; execução final dos testes do PR #127 continua pendente. Nenhuma integração, publicação ou alteração editorial de produção foi realizada.
