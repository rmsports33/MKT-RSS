# Integracao MKT-RSS publicador unico — 08/11/2026

Pedido: executar a integracao dos patches e preparar homologacao no ambiente real.

## Estado confirmado

- PR MKT-RSS #43 integrado na branch de trace, merge `e322384457053e8fd3efc0c164370c0472020f07`.
- PR Gate #65 integrado na branch RC3, merge `a8b795e249baeee4d4048d61ca9c1f82023e6f34`.
- Esta integracao concilia a master MKT-RSS com a branch de trace. Conflitos em AGENTS.md e pipeline_rss.py resolvidos mantendo prioridade MKT-RSS, contrato versionado e pesquisa gratuita de imagens; handoff-only nao busca imagem remota.
- Codigo e testes de stock_media_workflow, image_handler e prioridade_editorial da master preservados. Nenhum arquivo removido nem alteracao de workflow nesta conciliacao.
- PASSOU: 148 testes do conjunto pipeline/handoff, DNA, prontidao, midia, prioridade, broker, trace, SEO e drafts; 5 subtestes tambem passaram.
- PASSOU: suite ampliada, 329 testes; inicialmente uma expectativa da assinatura da API falhou e foi corrigida para verificar trace_run_id opcional e keyword-only.
- PASSOU: transporte contra nucleo Conexo OS fixado `b485d910c80501d64c5f15ab45366a61832fae17`, 20 testes; SKIP de 2 casos condicionais (PHP do host e consumidor PR43 nao configurados). A suite ampliada sem esse root pulava o modulo; nao confundir os dois resultados.

## Producao e bloqueio operacional

Leitura WordPress autenticada nesta sessao confirmou site ConexoTech, Gate RC2 inativo, Vault ativo e usuario Bot.editor ID 4 com perfil editor. Logo, nao e necessario criar duas contas novas. O administrador ID 3 permanece identidade separada; nao presumir autoria de aprovacao com base no papel.

O executor Cloud nao tem segredos ou variaveis WordPress/Turso configurados. O conector WordPress permite listar plugins/usuarios, mas nao configurar allowlist privada do broker, criar Application Password ou provisionar GitHub Secrets. Credenciais guardadas em Actions nao podem ser extraidas para esta sessao. Nenhuma materia foi aprovada ou publicada.

Preparados ZIP RC3 e ZIP RC2 de rollback a partir de Git. O arquivo RC3 tem SHA-256 `274bb16527426bef866070f79e78105ed24fd9b44f4b9a11b31d1e4a52dd1321`; rollback `1f43b5edb52b690c1d2efeafeea203c7beee4e3b0c5d396e232dd1f330ad564c`. Nao foram instalados nesta etapa.

## Proxima acao

Integrar esta conciliacao na master apos validacao. Para a operacao real, instalar RC3 com rollback preservado, configurar apenas Bot.editor no painel do broker e uma Application Password exclusiva no ambiente existente do MKT-RSS. Nao ativar Gate sem configuracao e homologacao, nem usar publicacao de artigo como teste tecnico. Finalize SEO estrito do broker continua bloqueado e pendente.

Recomendacao: validar primeiro a identidade do MKT-RSS por leitura autenticada no proprio ambiente Actions que ja guarda as credenciais; isso evita criar novo executor ou copiar segredos para o Cloud/chat.
