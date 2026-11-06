# Homologação de imagens gratuitas — implantação e rodada real (06/11/2026)

## Implantação na master
Política: bancos gratuitos e referência/licença verificada em primeiro lugar; IA somente quando busca gratuita executada não encontrar opção adequada. Não autoriza imagem RSS sem direitos, IA automática nem publicação.
- image_handler.py: commit 786c2e1af64875430a4254a882ed5011127dddbb
- pipeline_rss.py: commit d57356d1a5590fe89c699b17f2adcbf6aad38d25
- tests/test_image_stock_priority.py: commit 1aab8dd15566eed3325661727fe7236c2df1a069
Commits seletivos na master com [skip ci]; não houve merge amplo do PR #39.

## Testes reais da integração baseada na master
Branch isolada fix/free-stock-master-integration-20261106, SHA 9cfdb48039550fbb8ff11f79a7edd87e0fd55fcd.
- 7/7 testes novos PASS (pytest tests/test_image_stock_priority.py).
- 601 PASS, zero falhas (pytest tests) após instalar dependência prevista na CI python-telegram-bot>=21,<23.
- compileall passou. Primeira execução encontrou um erro de dependência Telegram (591 PASS, 9 SKIP, 1 FAIL); reteste com ambiente de CI correto passou.
Ambiente de teste Vercel temporário sem credenciais WP/Groq. Testes offline não validam busca real da API Unsplash nem visuais de tema.

## Fluxo real de mídia → WordPress draft
- Pauta: WordPress #9769, notícia da patente Microsoft; permaneceu draft.
- Foto Unsplash de Koen Sweers: https://unsplash.com/photos/a-microphone-in-front-of-a-computer-monitor-O6B3_2ylHLo
- Licença para usos editoriais/comerciais: https://unsplash.com/license . Conferida em 06/11/2026; imagem identificada como ilustrativa.
- Upload WordPress MCP confirmou mídia #9776 com título, ALT, crédito e fonte gravados.
- URL da mídia: https://conexotech.com.br/wp-content/uploads/2026/11/microfone-streaming-imagem-ilustrativa-microsoft-scaled.jpg
- Dimensões originais após processamento WordPress: 1743x2560; miniatura wide real 1200x675 e 90487 bytes.
- Associação ao post #9769 com featured_media=9776; readback autenticado: status=draft, modified=2026-11-06T17:31:11, featured_media=9776.
- Não houve publicação da notícia nem alteração do corpo do artigo.

## O que ainda NÃO está homologado
1. Fluxo automatizado integral do MKT-RSS: consulta Unsplash API → escolha/licença → upload → draft. A branch integrada consulta candidatos de modo opt-in quando CONEXO_RSS_PREVIEW_SOURCE_IMAGE=1 e a chave UNSPLASH_ACCESS_KEY existe; sem acesso informa PESQUISA_BANCO_PENDENTE. A seleção e o upload são supervisionados.
2. Inspeção do artigo privado no tema em 390px e 1440px. A captura pública da URL de draft não é prova de visualização autenticada. A existência da miniatura 1200x675 não comprova composição visual.
3. Autorização de publicação da versão revisada; nada nesta homologação a concede.

## Alerta de concorrência editorial
Durante a verificação final, WordPress #9696 (guia ANC) passou a status publish em 2026-11-06T20:31:16Z (17:31:16 BRT). Activity log atribui operação REST/MCP autenticada ao administrador, cliente openai-mcp, mas não identifica a conversa/automação. Não foi ação executada nesta tarefa. Não reverter automaticamente porque pode corresponder à atuação simultânea de outro operador.

## Conclusão
Implantação seletiva da política de imagens na master comprovada, suíte da master validada e um ciclo REAL de imagem gratuita → upload WP → associação privada → readback concluído. A homologação totalmente automática e a visual autenticada permanecem pendentes.


## Extensão E2E supervisionada — 06/11/2026, após a implantação inicial

**Módulo operacional criado:** `mkt_flow_p0/stock_media_workflow.py`, código testado na branch `feat/stock-media-e2e-supervised-20261106`, HEAD `56658996b352491c4f2c635624921e3a0a22d937`. Testes `tests/test_stock_media_workflow.py` cobrem upload REST de capa, processamento 1200×675, autor/licença/ALT, vínculo com rascunho, readback, proibição de origem RSS/URL arbitrária, ausência de revisão, mídia existente, postagem já publicada, erro de download e transporte. A chamada real exige arquivo JSON de imagem escolhida com revisão de direitos e visual marcadas por editor, confirmação CLI e credenciais WordPress no ambiente; por padrão, **não escreve**.

**Correção durante homologação:** preflight rejeitava erroneamente URL raiz HTTPS `https://conexotech.com.br`; corrigido na branch, antes da aprovação. Depois da correção: `python -m pytest -q tests/test_stock_media_workflow.py tests/test_image_stock_priority.py` **14 PASS / 0 FAIL**, e `python -m pytest -q tests` **608 PASS / 0 FAIL**, `compileall` PASS. Os testes utilizaram mocks, sem autenticação ou escrita WP reais do módulo novo.

**Implantação seletiva na master**, sem merge do PR #39 nem mudança do pipeline de publicação:
- `mkt_flow_p0/stock_media_workflow.py` commit `686c9d94d6203bfc337f5be1cbfe1653fe3d60ee`
- `tests/test_stock_media_workflow.py` commit `a33875eddf0ad33556a50d87f4536e11cbc78420`

Leitura GitHub após a cópia comprovou igualdade exata dos blobs entre master e branch aprovada (`a78fddcad6ed34389b2eb15a049dfdf5e3b88f0e` e `6a8aca55bf5ef7abf8f11b047a4a7f15b865a6f8`). O sandbox temporário expirou antes de uma nova execução diretamente no SHA da master; não atribuir à master um teste independente que não ocorreu. Cópia dos arquivos testados foi comprovada por hash.

**Readback WordPress ao encerrar:** post Microsoft **#9769** `draft`, `featured_media=9776`; post ANC **#9696** `publish`, `featured_media=9268`. Não houve nova escrita nos posts nessa extensão.

**Limite não resolvido:** nenhuma sessão de navegador autenticado disponível para renderizar o *draft* de Microsoft em 1440/390 px; portanto QA visual do **artigo privado** não foi concluído. O WP confirma imagem `conexo-wide` 1200×675, mas tamanho não substitui inspeção de enquadramento no tema. A rotina de busca automática de candidatos continua opt-in, com chave gratuita Unsplash necessária. O módulo novo oferece associação REST supervisionada depois de licença/visual explicitamente aprovadas, não decide automaticamente direitos de terceiros e não realiza geração IA. Não declarar publicação ou operação autônoma contínua.

**Próxima ação exata:** validar uma imagem e prévia em navegador WordPress autenticado com acesso ao draft, sem tornar o artigo público; depois executar o módulo CLI com aprovação específica em um novo draft **sem capa** e verificar readback, sob operador exclusivo. Não repetir o upload no #9769, que já possui mídia.


## Fechamento da integração de contrato de mídia — 06/11/2026

**Código reconciliado na master (mudanças seletivas):**
- `mkt_flow_p0/stock_media_workflow.py`: commit `295dd648496c081ee7f9c5b124db50f75b25759e`.
- `tests/test_stock_media_workflow.py`: commit `bf10e69060c0e5a25af25c661cc30b4f1bc3c1e1`.
- SHA testado diretamente no checkout da master após esses commits: `bf10e69060c0e5a25af25c661cc30b4f1bc3c1e1`.

**Correções de integração e segurança:**
1. A escolha de fotografia exige `approved_post_id` e `approved_post_modified_gmt` iguais à versão privada em edição; conteúdo alterado invalida o aceite anterior. O PHP/WP REST fornece `modified_gmt` no contexto de edição, independentemente da projeção resumida do WordPress MCP.
2. Verificação da mídia após upload: `GET /wp/v2/media/{id}?context=edit`, conferindo ID, texto ALT, crédito e referência de licença/origem.
3. Upload sem confirmação do ID e falhas de transporte são explicitamente indeterminados; sem retry automático para evitar imagens duplicadas.
4. Antes da associação, novo readback bloqueia se status, versão ou imagem destacada mudarem.
5. CLI `python -m mkt_flow_p0.stock_media_workflow --discover "termo"` pesquisa banco gratuito *sem escrever no WordPress*; caminho de anexação exige `--approved-photo-json`, `--post-id` e `--confirm-draft-media`.

**Evidências de teste da master (sandbox remoto, Python, sem segredo WP/Groq):**
- `python -m pytest -q tests/test_stock_media_workflow.py tests/test_image_stock_priority.py`: **21 PASS / 0 FAIL**.
- `python -m pytest -q tests`: **615 PASS / 0 FAIL**.
- `python -m compileall -q mkt_flow_p0 pipeline_rss.py`: **PASS**.
- Descoberta via CLI no checkout real, sem `UNSPLASH_ACCESS_KEY`: `IMAGEM_PENDENTE`, `PESQUISA_BANCO_PENDENTE`; não inventou inexistência de imagens nem acionou geração de IA.

**Prova real do destino WordPress e da entrega da mídia:** WordPress REST/MCP autenticado confirmou post **#9769** com `status=draft` e `featured_media=9776`, mídia **#9776** com ALT, crédito, página individual Unsplash e URL de licença. Requisições HTTPS de leitura à imagem em produção retornaram **HTTP 200, image/jpeg**, com decodificação Pillow **1200x675 RGB** para `conexo-wide` e **800x525 RGB** para `conexo-thumb`. Nenhuma escrita WordPress foi necessária na etapa atual.

**Limites verificáveis:** este turno não executou o CLI novo com credenciais WordPress reais em um novo draft e não autenticou navegador para visualizar o artigo privado em 1440/390 px. O E2E supervisionado por ferramentas já conectadas para #9769 foi comprovado anteriormente; as rotas Python de escrita permanecem validadas por mocks e pré-condições reais de leitura. Busca automática Unsplash continua precisando chave Free; falta de chave mantém pesquisa pendente em vez de sugerir IA. Nada aqui autoriza publicar ou agendar. Não declarar 100% da automação editorial ou da revisão visual.

**Próxima ação específica:** utilizar navegador autenticado com acesso a prévia privada para validar renderização desktop/mobile do draft; em outro draft específico sem capa e com revisão editorial concluída, executar o CLI autenticado em um operador exclusivo e conferir post + mídia por readback. Não sobrescrever #9769 nem usar imagem genérica potencialmente enganosa no comparativo Samsung #9681.


## Preflight final de autenticação e visual — 06/11/2026

Solicitação: executar o módulo Python com autenticação real e conferir o rascunho privado em 390/1440 px, sem publicar.

**Acessos efetivamente disponíveis no turno:**
- WordPress MCP autenticado: `GET` de post #9769 confirmou `status=draft`, `featured_media=9776`, modificado 2026-11-06T17:31:11; post #9681 segue `draft` sem capa.
- Projetos Vercel investigados sem revelar segredos: `conexo-jules-mcp-staging` e `conexotech-panel` não apresentam variáveis `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` para o módulo; `conexo-sftp-mcp` expõe nomes SFTP/WorkOS apenas, não as credenciais WP exigidas. O conector WordPress não transfere autenticação para um subprocesso Python.
- TinyFish Browser Context Profile padrão identificado, com `signed_in_sites=[]`; nenhuma sessão WordPress previamente autenticada para visualizar `/wp-admin/post.php?post=9769&action=edit` ou preview privada.
- API WordPress MCP pode ler o rascunho, mas não renderiza sua prévia privada autenticada em janelas de 390/1440. Screenshots públicos não provam esse requisito.

**Resultado honesto:** execução autenticada do novo CLI Python **NÃO realizada** neste turno por falta de acesso autenticado no ambiente de execução. A revisão visual do draft privado **NÃO realizada** por ausência de browser WordPress autenticado. Nenhuma imagem nova foi anexada e nenhum estado de artigo foi alterado. Não contornar com publicação temporária, credenciais copiadas manualmente no chat, nem falso PASS.

**Desbloqueio mínimo:** disponibilizar ao executor uma conexão autorizada com WordPress apenas no ambiente cloud, sem publicar os segredos na conversa, e salvar uma sessão de navegador autenticada que permita ler a prévia. Após isso: selecionar rascunho específico sem imagem e ficha de foto revista, rodar CLI único com confirmação explícita; conferir POST media, GET media, POST featured_media e GET post em status draft; capturar tema em 390 e 1440. Não reutilizar o draft #9769 como alvo de nova associação porque já contém capa.
