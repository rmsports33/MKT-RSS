# Revisão de integração e remediação — PR #127 (18/11/2026)

## Estado executivo

**Compatibilidade Git com a base: aprovada. Remediações de software propostas e versionadas. Homologação completa ainda pendente. PR continua draft.**

O trabalho atual avançou os três pontos anteriores:
1. MKT-RSS agora valida o marcador de proveniência com esquema tipado/estrito e o guard Python só considera `content.raw`.
2. Vídeo importado agora fica explicitamente `INSERIDO_AGUARDANDO_REVISAO_HUMANA`, sem declarar curadoria apenas porque os metadados estão presentes.
3. Há uma validação read-only de readback que compara o conteúdo bruto e renderizado do WordPress, além de um patch kit para centralizar a validação na RC10.4 do Gate real.

Entretanto, os testes MKT-RSS dessas alterações recentes ainda não foram executados no OpenCode, o patch RC10.5 ainda não foi aplicado nem validado numa cópia integral do plugin ativo e não há ambiente WordPress de homologação disponível para verificar filtros/renderização com escrita/readback. Nenhuma alteração foi aplicada ao site ativo.

## Gate WordPress real — descoberta que corrige o diagnóstico anterior

A leitura somente pela Hostinger API identificou o plugin ativo no site:
- `Conexo Editorial Gate (controlado)`, versão `0.1.0-rc10.4`.
- Núcleo: `wp-content/plugins/conexo-editorial-gate/includes/conexo-editorial-gate-core.php`.
- Fila/publicador: `includes/conexo-review-publisher.php`.
- Aprovação/owner review: `includes/conexo-owner-review.php`.

A RC10.4 já contém uma verificação parcial de `cxeg-package:v1` dentro de `cxgna_draft_readiness()`. Portanto, seria incorreto afirmar que o servidor não conhece o marcador. A lacuna real é que essa verificação de fila é incompleta e não está no validador central.

A fila atual remove ocorrências com `preg_replace`, decodifica um marcador, verifica o hash e alguns estados. Não exige unicidade estrita, campos exatos, tipos, versões/hash de versão, nem enums completos. A string `"false"` pode passar pela checagem de `empty()`.

Já `cxeg_quality_valid()` e `cxeg_quality_record()` não chamam o consumidor do marcador. Isso importa porque `cxeg_quality_valid()` é reutilizada por rotas de revisão, owner release e escrita/publicação. A proteção só na fila não garante todas as rotas.

## Remediação MKT-RSS versionada no PR

No branch `fix/editorial-import-provenance-video-20261118`:
- `mkt_flow_p0/editorial_provenance.py`: agora separa `validar_integridade()` de `validar()`, exige chaves exatas, tipos estritos, SHA-256 válido, mapa exato dos cinco módulos, estados conhecidos, voz/substância enumeradas e booleano real para direitos. O produtor também rejeita marca pré-existente duplicada ou inválida, módulos desconhecidos e nomes de módulos que não sejam strings, mantendo idempotência somente para uma marca íntegra.
- `editorial_publish_gate.py`: valida proveniência do conteúdo bruto e usa `content.raw`, não `content.rendered`; normaliza os objetos REST de título/conteúdo/excerpt usando raw somente.
- `editorial_wordpress_adapter.py`: acrescenta readback read-only que exige explicitamente `content.raw` e `content.rendered`; string plana do conector é inconclusiva/bloqueada. Verifica integridade raw e conservação de iframe/VideoObject entre raw e rendered; não faz HTTP por si.
- `mkt_flow_p0/editorial_import.py`: deixa a curadoria de vídeo pendente até revisão humana explícita e exige booleano real em `media_rights_confirmed`.
- Testes adicionados para esquema estrito, raw versus rendered, strings planas do conector, rights boolean, estado pendente de vídeo e rejeição de marca duplicada/inválida na origem. Os testes novos aguardam execução no HEAD atual.

**Esses testes ainda não foram executados após as alterações recentes.** O último conjunto de regressão reportado pelo OpenCode (288 passed, 0 failed, 10 subtests) corresponde ao SHA anterior `67116a57e4e00561574ea398e6ff7b3976281275`, não ao HEAD atual deste branch. Não atribuir esses resultados às novas mudanças.

## RC10.5 patch kit no repositório do site

Branch: `fix/gate-package-provenance-rc10-5-20261118` em `rmsports33/-site-conexotech`.

Diretório: `ops/gate-provenance-rc10.5/`.

Contém consumidor PHP estrito, 17 casos de contrato, aplicador de patch, três testes automatizados do aplicador e README. O patch exige proveniência apenas para posts com `_conexo_mkt_rss_run_id`; drafts legados sem esse vínculo permanecem no fluxo humano. A integração é centralizada em `cxeg_quality_valid`, `cxeg_quality_record` e `cxgna_draft_readiness`. Não altera checklist humano, owner release, HMAC, SQL guard, publicador nem cron.

Validação executada localmente com PHP CLI 8.4.24:
- 17 casos contratuais do helper: PASS.
- PHP lint do helper: PASS.
- Fixture sintético com funções/âncoras: dry-run, aplicação, lint do core/publisher sintéticos e repetição dos 17 casos: PASS.

**Limite importante:** isso não é a aplicação numa cópia integral da RC10.4, não é teste de todas as rotas WordPress e não é homologação da instalação ativa. A cópia integral do plugin deve ser obtida pelo OpenCode em diretório temporário e validada conforme o README, sem tocar em `public_html`.

## Curadoria de vídeo

O importador deixou de afirmar que a presença de ID/título/canal significa curadoria humana. O novo estado é `INSERIDO_AGUARDANDO_REVISAO_HUMANA`, com `human_curation_confirmed=false` e `human_review_required=true`. `human_acceptance` continua `PENDING` e `publication_authorized=false`.

Não existe ainda um atestado humano/versionado de todos os critérios da política (canal, aparelho em uso, jabá/clickbait e permissão de incorporação). O código não presume que alguém assistiu ao vídeo.

## Readback WordPress

O WordPress connector em contexto edit retornou o campo `content` dos posts consultados como string única; não forneceu o par `content.raw` / `content.rendered` necessário para comprovar a sanitização do iframe e do JSON-LD. Um post publicado existente foi apenas lido e não contém a nova marca nem vídeo; não é fixture válido para esse ensaio.

O staging do projeto foi removido. Nenhum rascunho de teste foi criado e nenhum POST/PUT foi feito no site ativo. O teste de persistência de iframe/VideoObject fica **inconclusivo / não homologado** até haver instância WordPress isolada com o mesmo papel e filtros.

## Compatibilidade com mudanças posteriores

A base do PR continua `3901ca0`. Os PRs #125 (normalização de títulos REST) e #126 (adaptador Gemini) já estão na base; seus quatro blobs continuam idênticos aos heads validados. PR #128 é documental e não tem caminhos em comum. PR #124 permanece divergente e não foi usado. Nenhum conflito de ancestralidade foi encontrado.

## Próximas verificações exigidas pelo OpenCode

No checkout isolado da branch MKT-RSS:
1. confirmar o HEAD atual;
2. executar os dois testes de regressão de tabela, quatro módulos focados e bateria relevante que foram usados anteriormente;
3. executar todos os novos testes de `test_editorial_provenance.py`, `test_editorial_import_video_provenance.py`, `test_editorial_publish_gate.py` e `test_editorial_wordpress_adapter.py`;
4. comparar baseline apenas se falhas, sem enfraquecer testes;
5. registrar SHA, Python, comandos e saída.

Para o Gate:
1. copiar a RC10.4 por leitura/cópia para diretório fora do document root;
2. rodar dry-run e patcher apenas na cópia;
3. guardar hash/backup/diff, rodar 14 casos e `php -l`;
4. validar a cópia integral com testes/mocks de qualidade, owner release e write preflight sem efetuar escrita;
5. não carregar/deployar a cópia no site.

Para WordPress readback: obter ambiente isolado com mesmo PHP, filtros, papel/capacidades e REST edit context raw/rendered. Sem isso, não declarar homologação.

## Decisão

PR #127 continua aberto e draft. Não fazer merge nem deploy ainda. A remediação do código está versionada, mas precisa de teste no novo HEAD, validação em cópia integral do Gate e prova de readback WordPress isolado.

Nenhuma mudança foi aplicada no site ativo, WordPress, Turso, cron ou produção.


## Atualização de revisão conjunta — 18/11/2026

### Validação técnica no HEAD atual

HEAD final MKT-RSS: 5406b076b823243490ea1fa937b758ba5f1577ae.
- tests/test_editorial_provenance.py: 43 passed.
- testes publish-gate/adapter/snapshot: 40 passed.
- tests/test_editorial_import_video_provenance.py: 10 passed.
- Exportador corrigido no commit 5406b07; fixture do produtor gerada (600 bytes), fingerprint 80d09ee7… e content hash 2d2c56ef…
- Evidência: https://github.com/rmsports33/MKT-RSS/pull/127#issuecomment-6992953782.

### Readback real reavaliado

As leituras GET edit/view de #9894, #9900, #9906 e #9253 correlacionaram ID/status/modified. Nenhum comprova o contrato requerido: #9894 não tem vídeo/marca; #9900 e #9906 não têm vídeo e usam fingerprint anterior; #9253 conserva componente cxaf-video com script lazy-load, mas não tem iframe persistido nem JSON-LD VideoObject. Além disso, o conector achata content em string e não fornece content.raw/content.rendered como objetos. A homologação de sanitização/persistência de vídeo continua pendente. Detalhes em docs/WORDPRESS_GATE_PROVENANCE_READBACK_20261118.md.

### Parecer conjunto

- Aprovado em cópia isolada: contrato Python, fingerprint compartilhado e exportador de fixture.
- Aprovado nos testes focados reportados: 93 testes (43 + 40 + 10).
- Pendente: readback real de iframe + VideoObject via REST nativo ou WordPress isolado.
- Sem autorização nesta revisão: merge, deploy, upload, escrita WordPress/Turso, aprovação, publicação, cron ou alteração da instalação ativa.

O PR #127 permanece draft até a pendência de readback ser resolvida e a revisão final aceitar o escopo integrado com o Gate #79.

## Retificação de estado — ensaio controlado de vídeo (18/11/2026)

Esta seção prevalece sobre os trechos históricos acima que ainda classificam a persistência de vídeo como pendente ou não homologada.

- O ensaio autorizado no rascunho temporário #9907 passou para persistência/conservação funcional: GET em context=edit e context=view conservaram iframe YouTube nocookie, JSON-LD VideoObject, marcador RC10.5 e o mesmo ID/status/modified. O SHA-256 do corpo raw correspondeu ao content_sha256 do manifesto.
- O post #9907 foi movido para a lixeira (status=trash). A purga definitiva ainda depende do wp-admin; não houve alteração em outros posts.
- Portanto, a persistência funcional de vídeo NÃO é mais bloqueio. A única pendência WordPress é estrutural: obter, por GET REST nativo via OpenCode, os objetos content.raw e content.rendered e executar offline o adaptador com esse envelope real. O MCP achata content em string e não fecha essa última prova.
- A evidência detalhada está em docs/WORDPRESS_GATE_PROVENANCE_READBACK_20261118.md e no comentário https://github.com/rmsports33/MKT-RSS/pull/127#issuecomment-6993604869.

**Estado operacional permanece inalterado:** PR #127 draft; nenhum merge, deploy, cron, aprovação, publicação ou alteração adicional no WordPress. Não iniciar integração do Gate até concluir o GET nativo e a revisão final dos HEADs/diffs.

## Revisão corretiva adicional do adaptador — 18/11/2026

Na revisão estática posterior aos 93 testes focados já reportados, foram endurecidos dois pontos de compatibilidade/robustez no parser de readback de vídeo:

- O parser agora reconhece `VideoObject` quando o JSON-LD usa `@type` como lista (por exemplo, `["VideoObject", "CreativeWork"]`) e quando o objeto está dentro de `@graph`. Essas são formas válidas de estruturar JSON-LD e não devem gerar falso bloqueio quando o iframe e o embedUrl correspondem.
- A leitura da porta da URL foi movida para dentro do tratamento de `ValueError`. URLs com portas inválidas ou fora do intervalo passam a ser classificadas como marcação de vídeo inválida, sem escapar como exceção inesperada do parser.

Foram acrescentados dois testes de regressão em `tests/test_editorial_wordpress_adapter.py` para essas situações. **Esses dois testes novos ainda precisam ser executados no OpenCode**; não são incluídos retroativamente nos 93 testes já reportados. Nenhuma chamada de rede ou escrita WordPress foi introduzida. A revisão não altera as regras de autorização: aprovação humana, proveniência, integridade raw e correspondência de vídeo continuam obrigatórias.


## Validação do campo uploadDate do vídeo — revisão estática

O campo opcional `youtube_uploadDate` era aceito como qualquer string não vazia e poderia chegar ao JSON-LD como data inválida. O importador agora aceita somente data ISO-8601 válida (`YYYY-MM-DD`) ou data/hora ISO-8601 com fuso explícito (por exemplo, `2026-10-01T12:00:00Z`); data impossível, texto livre e data/hora sem fuso são recusados. Foram adicionados casos válidos e inválidos em `tests/test_editorial_video.py`.

A validação confirma apenas o formato e a validade calendárica, não a veracidade da data publicada pelo canal. A origem factual continua sujeita à verificação editorial humana. Os novos testes de data também aguardam execução no OpenCode e não fazem parte dos 93 testes anteriores.

A ausência explícita (`null`) continua válida para esse campo opcional e é tratada como campo omitido; foi acrescentado teste de regressão para preservar essa compatibilidade.
