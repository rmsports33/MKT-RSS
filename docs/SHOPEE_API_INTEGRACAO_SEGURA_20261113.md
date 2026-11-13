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

## Atualização de homologação — Explorer real em 13/11/2026

O proprietário demonstrou com captura de tela que a sua conta Shopee tem status **Meu API Válido** e que a consulta read-only `productOfferV2` executou com **HTTP 200** e retorno `data.productOfferV2.nodes`. O schema do Explorer autenticado confirma filtros opcionais `itemId: Int64`, `shopId: Int64`, `page: Int`, `limit: Int`, além de `price: String`, `priceMin: String`, `priceMax: String`, `shopName`, `productName`, `productLink` e `offerLink`. Portanto, a frase anterior “schema precisa ser confirmado” foi superada **para esses campos**.

No registro visível, item ID `58217601055`, loja ID `728389176`, vendedor `MAQ TOOLS`, `price=priceMin=priceMax=95.99`, link de produto oficial. Esses são **dados de exemplo observado no Explorer**, não prova de que o MKT-RSS recebeu a resposta com suas próprias credenciais.

O módulo `mkt_flow_p0/price_collector.py` foi corrigido para selecionar `price` e exigir igualdade com `priceMin` e `priceMax`. Seu status de procedência passou a `VERIFICADO_API_OFICIAL`. A validação genérica aceita esse status além de `VERIFICADO_NA_PAGINA`; permanece exigindo nome do produto exato, loja identificada e URL HTTPS. Uma divergência bloqueia gravação de evidência.

Foi criado `scripts/shopee_readonly_preflight.py`, um **teste interativo de uma única chamada** que importa o módulo real do MKT-RSS, pede App ID e senha via `getpass` sem eco nem flags de CLI, e imprime somente dados públicos da oferta. Não escreve WordPress, Turso, Drive ou SQLite. Deve rodar somente num terminal privado autorizado, com Python e `requests` já disponíveis, **fora de public_html**, sem GitHub Actions, sem salvar transcrição do terminal. Exemplo:

```sh
python scripts/shopee_readonly_preflight.py --item-id 58217601055 --shop-id 728389176
```

Para ser executado, o diretório precisa conter clone do repositório `MKT-RSS` com o script e seu módulo importável; nenhum deploy foi realizado. **Não publicar credenciais em mensagens, repositórios, terminal com histórico de comandos ou capturas**. Se a autenticação da API falhar, não tentar repetidamente; verificar a conta e o schema.

Regressões locais offline após atualização do coletor: **9/9 testes PASS** (consulta assinada simulada, incoerência e ausência de `price`, IDs incorretos, GraphQL error, sem credenciais) e `py_compile` do módulo/testes/script PASS. Nova regressão baseada na forma da resposta do Explorer acrescentada depois, ainda requer execução conjunta para ser declarada PASS.

### Aceite — distinguir três níveis
- **API Shopee na conta: CONFIRMADA.** HTTP 200 e resultado real no Explorer.
- **Adaptador MKT-RSS: PREPARADO E TESTADO COM MOCK.** Nenhuma execução real autenticada do próprio Python MKT-RSS foi feita.
- **Conexão MKT-RSS ↔ Shopee: PENDENTE DE HOMOLOGAÇÃO REAL.** Falta execução de um preflight em terminal autorizado com credenciais inseridas diretamente pelo proprietário e saída pública correspondente; implantação de rotina/armazenamento somente depois, sem bloquear o Gate.
