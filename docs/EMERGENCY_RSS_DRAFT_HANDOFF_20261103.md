# Desbloqueio emergencial: RSS → rascunho WordPress

Data: 2026-11-03. Objetivo: retomar geração e gravação de rascunhos, sem ativar o Gate de publicação ou migrar SEO.

## Diagnóstico comprovado

- No pipeline_rss.py, processar_item gerava e auditava o texto, mas terminava incondicionalmente com acao=bloqueado e escreveu=false, inclusive para rascunho.
- No WordPress em produção, o conector criou o draft técnico #9752, atualizou seu conteúdo, confirmou status draft e enviou o teste para a lixeira. Não publicou.
- A nova função mkt_flow_p0/wp_draft_staging.py grava somente draft: HTTPS, slug determinístico por URL da fonte, consulta de duplicata, readback e sem retry automático.
- A publicação continua sujeita à revisão factual/substantiva e autorização humana; metadados SEO consultivos não equivalem à aprovação.

## Ativação — apenas no executor real autorizado

1. Deploy da branch testada do PR #39 no executor Python efetivamente em uso. Commit GitHub isolado NÃO altera o runtime.
2. Configurar CONEXO_RSS_DRAFT_STAGING=1 como flag no runtime privado. Usar WP_URL=https://conexotech.com.br, WP_USER e WP_APP_PASSWORD que já estejam configurados. Nunca divulgar credenciais ou persistir em Git.
3. Executar um único item de RSS e confirmar ID, status draft, título, corpo e referência à fonte no WordPress.
4. Reexecutar o mesmo item e exigir o mesmo ID sem segunda criação, sem sobrescrever a edição humana.
5. Se ocorrer timeout, verificar o slug no WordPress antes de repetir. Nunca iniciar publish/retry automático.

## Rigor proporcional

Rascunhos são insumos não revisados. Revisão editorial, checagem de fontes, imagem com direitos verificados, links internos e aceite da versão são necessários ANTES de publicar, não para armazenar um rascunho privado. Não importar automaticamente imagens da fonte sem verificar direitos.

A versão SEO 0.5.2, o Gate experimental, staging e Hostinger MCP NÃO são pré-requisitos para operar o WordPress supervisionado existente. O Rank Math permanece ativo. Não usar GitHub Actions como executor obrigatório.

## Evidência e limitação

A suíte de testes Python no PR #39 valida criação, idempotência, colisão de slug, recusas e erros de transporte com mocks. A conexão WordPress foi testada diretamente, mas o novo pipeline Python AINDA NÃO foi implantado e executado contra o WordPress real. Não declarar a missão 100% até observar geração → draft real → revisão → publicação autorizada com readback.