# MKT-RSS — Shopee Affiliate Open API: preparação segura (13/11/2026)

## Inventário de execução comprovável
- `rmsports33/MKT-RSS/.github/workflows/daily.yml` possui coleta RSS agendada (GitHub Actions, 09h BRT); `rss-homolog-manual.yml` permite execução manual. **Não disparar Actions** para validar Shopee.
- Hostinger: conector encontrou site WordPress `conexotech.com.br` e **zero cron jobs** para conta `u401421381`; isto não exclui outros executores externos, mas **não comprova** que MKT-RSS Python rode na Hostinger.
- Vercel: projetos da conta consultada não incluem projeto chamado MKT-RSS; `vercel.json` do repositório não comprova deploy.
- `fly.toml` declara `mkt-rss-bot`, processo `python admin/bot.py` (Telegram), **não** pipeline RSS nem coletor de preços. Status de Fly.io não foi comprovado por conector.
- Conclusão: os workflows GitHub são a evidência de agendamento disponível; a localização de um processo Python independente de Actions ainda é desconhecida.

## Credenciais
Usuário relatou Shopee `Meu API Válido` e App ID/Senha API disponíveis. **Nunca colar tokens no chat, documentos, GitHub ou PR**. Os nomes do módulo de preços existente são `SHOPEE_PARTNER_ID` e `SHOPEE_PARTNER_KEY`. Quando houver **executor cloud real** autorizado, configurar essas duas variáveis como segredos **do próprio runtime**, em um painel de variáveis secretas, nunca arquivo versionado. A utilidade antiga `-site-conexotech/tools/2026-10-03_shopee_openapi.py` usa nomenclatura diferente (`SHOPEE_APP_ID`, `SHOPEE_SECRET`); não duplicar credenciais ou serviços. Usar nomes do módulo que realmente executa. Se o executor for alterado, fazer mapeamento seguro na inicialização, não manter dois clientes concorrentes.

## Código implementado
Arquivo `mkt_flow_p0/price_collector.py`: `_coletar_shopee(item_id, shop_id)` agora implementa **consulta GraphQL assinada em modo somente leitura** a `https://open-api.affiliate.shopee.com.br/graphql`. Header SHA256 = hash(AppId + Timestamp + corpo JSON exato + Secret). Query `productOfferV2` com filtro `itemId` e `shopId`, retornando `productName`, `priceMin`, `priceMax`, `productLink`, `shopName`. Exige IDs numéricos, correspondência única de item e loja, preço mínimo igual ao máximo, moeda BRL, nome, vendedor e URL HTTPS. `coletar_preco_produto` também exige nome completo exatamente igual ao esperado antes de aceitar evidência. Retornos nulos ou erros GraphQL não são tratados como preços válidos.

**ATENÇÃO**: os nomes exatos dos parâmetros/campos de `productOfferV2` **ainda precisam ser confirmados no Explorer oficial autenticado da conta** antes de teste real. Documentações públicas de terceiros descrevem esse formato, mas não substituem homologação do schema autorizado da conta. A consulta não gera links curtos, não publica e não escreve no WordPress. A função genérica de coleta pode registrar evidência em SQLite quando invocada — logo, testes reais só depois de definir armazenamento persistente autorizado.

## Provas sem Actions
`tests/test_shopee_api_readonly.py`: 7 testes isolados **PASS** no Python local do ambiente de auditoria, com resposta mockada: assinatura, identidade item, identidade loja, preço variável, erro GraphQL, ausência de credenciais e IDs inválidos. `py_compile` de ambos os arquivos **PASS**. Nenhuma chamada real à Shopee, GitHub Actions, WordPress ou banco; nenhum segredo real manuseado.

## Homologação gradual
1. No navegador autenticado do proprietário, abrir https://open-api.affiliate.shopee.com.br/explorer/v2 ; usar credentials APENAS nessa página oficial e executar consulta **read-only** de produto; confirmar schema `productOfferV2`, parâmetros e campos `nodes`. Não acionar `generateShortLink`, mutações ou alteração de links.
2. Confirmar o ambiente Python persistente **já existente**, com acesso de escrita restrito ao próprio runtime, sem criar novo cron, serviço ou Actions. Caso não exista, registrar lacuna e decidir explicitamente sobre executar sob demanda, antes de automatizar.
3. Adicionar segredos via painel do runtime (`SHOPEE_PARTNER_ID`, `SHOPEE_PARTNER_KEY`) e rodar UMA consulta autenticada supervisionada. Não incluir valores em logs.
4. Inspecionar se produto/variante, IDs da Shopee, vendedor, preço e URL conferem. Se oscilam ou houver faixas de preço, marcar `REVISAR`; não atualizar WordPress.
5. Registrar evidência no histórico privado de ofertas já existente no Drive e fazer readback. Só depois considerar agendamento; nenhuma publicação ou preço WordPress automática.

## Referências
- Portal oficial autenticado: https://affiliate.shopee.com.br/open_api
- Explorer oficial: https://open-api.affiliate.shopee.com.br/explorer/v2
- Contrato público ilustrativo (terceiro, não autoridade): https://www.affiliateshopee.com.br/documentacao
