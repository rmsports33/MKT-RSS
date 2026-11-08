# Integração da escrita editorial — 30/10/2026

Depende do núcleo da PR conexo-os #42 e do MU-plugin do site. O lock fixa os hashes
do validador, assinador e diretrizes; ausência/divergência bloqueia a importação.
Não baixa código nem instala dependências na execução do publicador.

A PR #33 avançou durante esta correção para a3fe347e: o parâmetro revisao_factual
e as duas contraprovas de publicação direta foram preservados. Esta entrega usa
uma branch dependente para não sobrescrever a sessão que continua naquela PR.
Flags de factualidade do chamador continuam insuficientes para liberar escrita.

## Operação supervisionada após instalação autorizada

Usar o checkout do núcleo correspondente ao lock. Configurar no executor confiável
WP_URL=https://conexotech.com.br, WP_USER, WP_APP_PASSWORD e
CONEXO_EDITORIAL_GATE_KEY; a mesma chave precisa estar no servidor. Não colocar
valores no pacote, prompt, histórico de shell ou Git. O ator é o ID real da conta
WordPress autenticada, não necessariamente o autor humano do artigo.

O pacote RSS inclui payload.discovery com pauta_id e source_url correspondentes
à origem apurada. A descoberta e o ranking não aprovam o artigo. A apuração e a
revisão separada permanecem reais e supervisionadas, sem chamada automática a IA.

```bash
python pipeline_rss.py --editorial-package editorial/artigo.json --core-root /checkout/conexo-os --actor-id ID_REAL --intent stage
```

stage cria apenas draft técnico privado. Não marca entrega, publicação ou pauta
concluída. Após receber ID, atualizar a ficha, conferir tema desktop/mobile e
revisar a nova versão. Em seguida usar --intent draft; após aceite e ordem
específica, --intent publish ou --intent schedule --publication-reference
REFERENCIA_REAL. A data GMT de schedule fica no payload revisado e deve ser
mais de dois minutos futura. Esses exemplos são operações futuras, não execução
ou autorização atual. Os quatro artigos existentes continuam incompletos.

Timeout devolve nonce; repetir somente a consulta com --operation-nonce NONCE.
O cliente não faz novo POST nesse modo. RESERVED ou divergência exige inspeção.
Não criar outra operação para contornar falha. Leituras exigem a conta correta.

O wrapper publicar_no_wordpress exige pacote e núcleo. Não baixa imagem, altera
tags ou grava Rank Math depois de aprovar a versão. Os IDs de mídia e categorias
devem estar previamente conferidos na ficha. O cliente MCP legado aceita somente
ferramentas de leitura; CPTs não ganham um caminho alternativo de escrita.

## Testes offline executados

46 testes direcionados passaram, incluindo os dois testes novos da outra sessão,
e o percurso Python → assinatura → PHP real → adaptador WP em memória. Não houve
HTTP ao site. Configure CONEXO_TEST_CORE_ROOT e PYTHONPATH para o checkout do núcleo.
Para o teste PHP, configure CXEG_WASM_RUNNER, CXEG_TEST_SITE_ROOT e CXEG_WASM_MODULES
conforme README do MU-plugin. A execução registrada usou essas variáveis, sem skips.
Sem o núcleo, essa suíte de integração é explicitamente ignorada; isso não prova
homologação. Não foi executada a suíte integral do MKT-RSS nem CI faturável.

```bash
python -m pytest tests/test_editorial_transport.py tests/test_editorial_publish_gate.py tests/test_editorial_wordpress_readiness.py tests/test_wp_publish_no_bypass.py tests/unit/test_wp_publisher_p0.py -q
```

Ainda não instalado, integrado à master ou homologado no WordPress/Jetpack real.
Não afirmar bloqueio remoto a partir do cliente ou desses testes isolados.

O teste de descoberta usa SQLite real e os fontes das PRs MKT-RSS #32 e Conexo OS #43 (3bd50bab / 692ad488), sem reimplementar o adaptador. Configure CONEXO_TEST_DISCOVERY_CONSUMER para o arquivo do consumidor fixado; sem essa dependência, o teste é explicitamente ignorado. A execução registrada teve zero skips. As fontes de descoberta foram sobrepostas apenas no checkout de teste, sem copiá-las para esta branch.


## Integração de SEO privado — 03/11/2026

O WordPress já opera com Conexo Native SEO **0.5.1**, mas essa informação é
distinta da homologação de materialização de contratos privados. Rank Math
permanece ativo, sendo apenas um transportador temporário de metadados.
O usuário confirmou que o UpdraftPlus exibe conjuntos de backup completos;
a **restauração isolada ainda não foi testada**.

Foi acrescentado `mkt_flow_p0/seo_delivery_signing.py` com a função pura
`prepare_signed_seo_contract`. Ela não toca na rede, não escreve WordPress e
não aprova conteúdo por conta própria. Requer: pacote editorial `stage=ready`,
SEO declarado dentro do pacote aprovado, resultado já conferido pelo transporte
autenticado do Gate com `intent=publish`, mesmo `version_sha256`, snapshot
publicado com conteúdo, título, slug e ID idênticos; canonical real e chave
privada exclusiva de no mínimo 32 bytes. A assinatura usa HMAC-SHA256 sobre o
JSON canônico `conexo-seo-v1`, compatível com o verificador PHP do Conexo SEO.

### Falta fechar o circuito remoto

**Bloqueio real identificado no código atual:** o `Conexo Editorial Gate`
instalado mas inativo impede escrita genérica de post meta quando ativado.
Atualmente o canal protegido só permite a imagem destacada durante a escrita
assinada; por isso **não basta** gerar um contrato SEO assinado no Python.
É necessária uma operação de materialização **dentro do Gate** que:

1. Confirme o nonce de uma publicação `COMPLETE` do operador autenticado,
   compare o snapshot atual com o snapshot aprovado e valide também a versão
   do conteúdo no WordPress.
2. Exija o contrato SEO assinado com uma chave exclusiva do servidor e
   canonical idêntico a `get_permalink(post_id)`, title/description já
   vinculados ao pacote revisto.
3. Autorize exclusivamente a meta privada `_conexo_native_seo_contract`
   dentro desse contexto e faça readback da meta salva, com idempotência.
4. Não aceite promoção da meta REST `_conexo_native_seo_draft` nem bypass por
   chamadas diretas de `wp/v2/posts` ou pelo MCP legado.
5. Seja testada em execução isolada antes de ativar o Gate no site público.
   Nunca instalar segredos em commits ou comentários GitHub.

**Sem implementação dessa rota restrita, não ativar o Gate** nem
`CONEXO_RANKMATH_BRIDGE_OUTPUT`. Não desligar Rank Math. Não transformar
a existência do backup em prova de restauração testada.


## Escopo de conectores e desbloqueio da operação (03/11/2026)

**Conector Hostinger MCP fora do mecanismo.** O executor confia no pacote
editorial revisado, na autenticação REST WordPress e nas permissões do Conexo
Editorial Core; não há etapa de descoberta, autorização ou publicação dependente
do conector Hostinger. Nenhuma falha desse conector pode ser considerada bloqueio
do pipeline, nem deve ocasionar novas tentativas de sua configuração.

**Trilha já operável:** ChatGPT-first produz material revisável, o WordPress
autenticado mantém rascunhos, e a publicação permanece supervisionada com revisão
factual/substantiva e aceite da versão. O Gate permanece desligado enquanto a
homologação separada não estiver comprovada.

**Trilha de migração:** PR #37 insere o SEO consultivo no pacote antes da revisão
e recalcula o hash; PR #35 publica somente pelo transporte autorizado e, no
modo estrito opt-in, testa o readiness do WordPress; PR #58 fornece Gate e ponte
SEO em código de branch. Backups UpdraftPlus existentes foram informados pelo
usuário, mas restauração testada e configuração privada de chaves ainda precisam
de evidência. O conector Hostinger não é uma dessas pendências.

Referência canônica de implantação e rollback: Conexo OS PR #46,
`docs/CHATGPT_FIRST_WORDPRESS_UNIFICATION_20261103.md`. Sem merge, deploy,
publicação ou segredo neste registro.
