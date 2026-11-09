# Pesquisa a partir da fila efetiva — 09/11/2026

## Evidência anterior

O daily usa TURSO_DATABASE_URL/TURSO_AUTH_TOKEN do repositório, sem environment.
Run schedule 42504925429, 08/11: credenciais mascaradas presentes, resultado
novas=0/duplicadas=2/falhas=[], sem DB local para artifact. Isso indica Turso nessa
execução, não uma fila SQLite disponível neste checkout. O banco de homologação
é configuração distinta e não representa automaticamente a fila do daily.

Usuário autorizou explicitamente localizar e consultar a fila efetiva em leitura.
A restrição histórica de não usar o banco principal para testes de escrita é
preservada: nenhum schema/INSERT/UPDATE/DELETE ou alteração editorial nesse banco.
Não copiar segredos entre ambientes, não revelar valor/hostname da configuração.

## Fluxo implementado

1. Job sem environment lê as MESMAS variáveis do daily. Verifica URL de serviço
   Turso HTTPS/libsql, host .turso.io, sem userinfo/porta/path/query/fragment; sem
   configuração completa recusa, nunca fallback SQLite. Dois SELECTs: tabela e
   até 50 linhas DESCOBERTA da fonte Tecnoblog, mais recentes primeiro.
2. Confere ID canônico de 32 hex, URL HTTPS Tecnoblog, estado e data de publicação
   até 168h, nunca data de criação para renovar notícia. Extrai UMA entidade
   literal do título por padrões de família/modelo, sem lista de aparelhos datada.
   Não pesquisa comparativo com várias entidades ou assunto ambíguo por inferência.
   Primeira linha adequada é candidata de pesquisa, não prioridade de publicação.
3. Somente referência de fonte já publicada (URL/ID/data), entidade literal e
   fingerprint da configuração passam ao segundo job. Nenhum título completo,
   resumo, texto de artigo, consulta SQL privada ou segredo. Esses metadados de
   fonte/consulta aparecem no log público; séries completas ficam privadas.
4. Segundo job usa exclusivamente rss-homolog/token existente e host fixo para
   guardar evidência. Recusa se o alvo for o mesmo banco lido pelo daily. Consulta
   BR now 7-d uma vez, HTTP sem navegador/fallback; salva série/contexto/identidade
   em tabela de evidências já existente e confere igualdade por readback.
   Referência de fila expira em 1h; publicação RSS também deve continuar recente.
5. Receipt registra queue_reference_verified_at_selection=true com horário e
   fingerprint; snapshot imutável de demanda não fabrica verificação atual da
   fila homolog. Estados podem mudar depois: não é reserva ou autorização.

Comando manual por Issue do proprietário:
`[daily-queue] pesquisar pauta existente`. Repositório público original, runner
padrão, limites 2+3 minutos, sem cron, artifacts/cache, escrita WordPress ou staging.
Mesmo segredo do repositório não é copiado para homolog: cada job recebe sua
configuração diretamente do respectivo escopo autorizado.

## Revisão e limites

Termo proposto é trecho literal de entidade do título, não o título inteiro.
Isso é rastreabilidade lexical, não revisão humana, ciclo comercial, apuração de
fontes, volume absoluto ou certificado de interesse suficiente. human_query_review
=PENDING e commercial_status=UNKNOWN. Não recomendar oferta/review de modelo só
porque esse termo possui índice positivo. Não promover estado ou publicar.

Se não houver linha recente com entidade única, informar o motivo; não criar
pauta artificial nem escolher produto antigo. Esse modo não cobre ainda notícias
sem produto explícito: exigir consulta editorial identificada para esses casos.

51 testes direcionados passaram: 31 com -S e 20 regressões. Oito novos verificam
origem real da configuração, somente SELECT, IDs/URLs, expiração, entidade ambígua,
variante Plus/Pro Max, estados terminais e fronteira entre banco diário/homolog.
Prova externa deve ser registrada separadamente; daily.yml continua idêntico.

## Ajuste orientado pelas fontes existentes

Leitura real no daily encontrou quatro pautas recentes e íntegras. Cobertura de
serviços foi acrescentada; o resultado continuou sem entidade inequívoca, então
foram conferidas as referências das fontes publicadas, sem alterar a fila.

Proposta assistida explícita para a linha já existente de ID
45ab798001543004f3a8e5ae0be5b7d9, sobre sugestões de palavras no iPhone:
consulta `teclado do iPhone`, intenção de pesquisa para possível guia duradouro.
Não reutilizar notícia de 06/11 como notícia recém-publicada, nem repetir a
alegação numérica do título sem apuração. A proposta é configuração editorial
rastreável ligada à URL exata; não uma aprovação humana ou ranking automático.

Antes do Trends, o executor consulta robots.txt da fonte e a página HTTPS
permitida, sem redirects, timeout 8s e 1MiB por resposta. Confere canonical e
presença dos termos iphone/teclado dentro de article, ignorando script/style.
Bloqueio de robots/rede/canonical/contexto interrompe, sem contorno. Isso demonstra
contexto lexical da fonte, não factualidade, revisão visual ou experiência própria.
Receipt preserva hash da resposta e flags, não texto copiado do artigo.

56 testes direcionados passaram após esta adequação (36 com -S e 20 regressões).
