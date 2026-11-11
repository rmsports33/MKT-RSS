# Conferência de vínculo com a fila — 09/11/2026

`demand_queue_binding.check_binding` valida primeiro o pacote privado existente,
depois consulta somente a existência da tabela rss_pautas e uma linha pelo ID.
Exige igualdade exata de ID e URL canônica já armazenada pelo registrar. Não
procura por título semelhante, não cria tabela/linha e não normaliza silenciosamente
URLs divergentes. Usa apenas dois SELECT parametrizados, sem inicializar fila.

Identidade conferida é separada de relevância: igualdade query/titulo é descrita
como EXACT_QUEUE_TITLE, não como demanda suficiente ou termo apropriado. Consulta
diferente exige revisão específica. topic_relevance_verified e publicação seguem
false. Estado terminal da pauta não muda e não se torna selecionável por este teste.
A verificação fica em receipt separado; não reescreve o snapshot original.

O modo `bind` do executor existente recupera o pacote privado anterior pelo
digest e realiza a conferência no mesmo Turso homolog. Host/URL exatos, segredo
rss-homolog existente, sem trocar ambiente ou copiar credenciais. Falha em tabela,
linha, leitura, ID/URL ou estado retorna motivo explícito. Não concluir que a fila
produtiva está quebrada por uma ausência no banco de homologação.

Acionamento por Issue exata do proprietário:
`[demand-evidence] verificar vinculo existente`. Job adicional no workflow já
existente, somente repo público original/runner padrão, limite de dois minutos,
sem artifacts/cache, novo cron, Trends, RSS, IA ou WordPress. Digest fixo corresponde
à evidência previamente recuperada; conteúdo da Issue nunca vira comando.

61 testes direcionados passaram: 46 com Python -S e 15 de fila/workflow.
Sete novos cobrem vínculo exato sem mudanças, tabela/linha ausentes sem criação,
URL divergente apesar de título igual, título alterado/estado terminal preservado,
credencial ausente, corrupção e falha remota sem vazar mensagem. Fixtures não
comprovam presença real de uma linha: resultado externo será registrado após execução.

Próximo passo depende do resultado real. Se houver vínculo, revisar o termo com
o assunto e as fontes, sem presumir aceite humano. Se faltar a linha no homolog,
manter evidência destacada e identificar uma pauta em ambiente autorizado por
leitura; nunca inserir uma linha de teste para alegar vínculo produtivo. Staging
continua desativado e não é requisito desta conferência.
