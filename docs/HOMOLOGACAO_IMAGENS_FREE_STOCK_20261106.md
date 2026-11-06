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
