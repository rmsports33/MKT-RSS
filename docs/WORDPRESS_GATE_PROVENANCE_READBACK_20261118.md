# Gate WordPress: integração da proveniência e readback — 18/11/2026

## Descoberta do Gate ativo

A leitura somente pela Hostinger API identificou no site \`conexotech.com.br\`:
- Plugin ativo: **Conexo Editorial Gate (controlado)**, versão **0.1.0-rc10.4**.
- Núcleo: \`wp-content/plugins/conexo-editorial-gate/includes/conexo-editorial-gate-core.php\`.
- Fila/publicador: \`includes/conexo-review-publisher.php\`.
- Revisão do proprietário: \`includes/conexo-owner-review.php\`.

Não houve escrita, upload, ativação/desativação, criação de rascunho, publicação ou agendamento no WordPress.

O código ativo não está versionado na árvore observada de \`rmsports33/-site-conexotech\`. Por isso, a correção é preparada como patch kit revisável, não como um plugin paralelo nem como uma cópia incompleta do plugin instalado.

## Estado parcial encontrado na RC10.4

O método \`cxgna_draft_readiness()\` de \`conexo-review-publisher.php\` já inspeciona \`cxeg-package:v1\`, compara um hash e exige módulos, voz, substância e direitos. Porém:
- remove todas as ocorrências com \`preg_replace\`, mas decodifica somente um marcador;
- não rejeita duplicatas completas/incompletas de forma consistente;
- não valida conjunto exato de campos, tipos estritos, versão SHA ou enumerações;
- \`empty()\` aceita alguns valores inesperados, incluindo a string não vazia \`"false"\`, como se fossem direitos confirmados.

Mais importante, o núcleo \`cxeg_quality_valid()\` não consome a marca. O endpoint \`cxeg_quality_record()\` também não a verifica antes de armazenar um parecer. A função central é reutilizada por rotas de revisão, owner release e escrita/publicação; portanto, a checagem isolada da fila não cobre todas as transições.

## Correção preparada — RC10.5 patch kit

Branch do repositório do site:
\`fix/gate-package-provenance-rc10-5-20261118\`

Diretório:
\`ops/gate-provenance-rc10.5/\`

Arquivos:
- \`conexo-editorial-provenance.php\`: consumidor PHP estrito do manifesto.
- \`test_conexo_editorial_provenance.php\`: testes contratuais independentes.
- \`apply_gate_patch.py\`: aplicador com âncoras exatas, dry-run obrigatório recomendado, backup e guarda explícita \`--isolated-checkout\`.
- \`README.md\`: instruções de cópia isolada e critérios de aceite.

O patch propõe três mudanças exclusivamente na cópia de validação:
1. incluir o helper no núcleo;
2. exigir a marca no \`cxeg_quality_valid()\` e \`cxeg_quality_record()\`;
3. substituir a lógica duplicada da fila pelo mesmo validador central.

Assim, a validação será repetida nas funções centrais que a revisão humana, owner release e fluxo de escrita já chamam. O aceite humano, o checklist, identidade do proprietário, HMAC, SQL guard, cron e publicador permanecem intactos.

A marca continua sendo um **recibo de integridade**, não uma assinatura ou certificado de identidade humana. Direitos de imagem e revisão factual seguem dependentes das etapas humanas/independentes já existentes no Gate.

## Validação já executada

Com PHP CLI 8.4.24:
- **17 casos contratuais** passaram no helper isolado.
- \`php -l\` passou para o helper.
- Um fixture sintético inicial foi usado durante o desenvolvimento. Depois dos últimos ajustes de escopo/ordem e da adição do teste reprodutível `test_apply_gate_patch.py`, os três testes automatizados do aplicador ainda precisam ser executados no HEAD atual. O patcher exige sentinel `.conexo-gate-isolated-copy` e recusa caminhos sob `public_html`, `www`, `httpdocs` ou `htdocs`.

Isso não é teste da cópia integral do plugin RC10.4 nem homologação na instalação ativa. A aplicação na cópia completa ainda deve ser feita pelo OpenCode, conforme o README do patch kit, e os resultados precisam ser registrados com SHA-256, PHP, saída de lint, testes e diff.

## Readback WordPress — pareamento dos contextos REST

O conector WordPress empregado pelo projeto achata cada chamada em uma string:
- `context=edit`: conteúdo bruto persistido;
- `context=view`: HTML renderizado para exibição.

Uma leitura somente do post #9894 foi executada nos dois contextos. Ambas retornaram o mesmo ID (9894), status (`pending`) e `modified` (`2026-11-16T22:42:42`). O corpo bruto teve 11.435 caracteres e o renderizado 11.447; os conteúdos não são idênticos, como esperado após a renderização. Nenhuma escrita foi feita.

Essa resposta não contém `cxeg-package:v1`, iframe YouTube ou `VideoObject`; portanto ela comprova somente que os dois contextos podem ser lidos e correlacionados para a mesma versão. Não comprova a proveniência MKT-RSS nem a preservação de vídeo.

### Correção do adaptador MKT-RSS

O adaptador agora inclui `assemble_wordpress_context_readback(edit_post, view_post)`, que converte as duas respostas em `content.raw` e `content.rendered` somente quando:
- os dois IDs são o mesmo inteiro positivo;
- os dois valores `modified` são presentes e idênticos;
- status é presente e idêntico;
- a chamada edit fornece corpo bruto não vazio e a chamada view fornece HTML renderizado não vazio.

O fluxo `inspect_wordpress_draft()` pode receber um segundo callback `fetch_post_view` para fazer as duas leituras. Sem os dois contextos, uma string achatada continua bloqueada. ID, versão ou status divergentes falham fechados. Foram adicionados quatro testes para o pareamento, rejeição de ID/versão divergentes e inspeção com as duas chamadas. **Esses novos testes ainda precisam ser executados no HEAD atualizado do PR #127.**

### Limite restante da homologação

Não foi identificado, entre as respostas reais consultadas até aqui, um post de prova que reúna marcador MKT-RSS válido, iframe `youtube-nocookie` e JSON-LD `VideoObject` já persistidos. Não será criado um post de teste na instalação ativa.

Para encerrar a homologação de vídeo, OpenCode deve:
1. localizar somente por leitura um post existente comprovadamente vinculado ao MKT-RSS e que contenha iframe + `VideoObject`;
2. obter a resposta de edição e a de visualização, preservando ID, status e `modified`;
3. executar o normalizador e `validate_wordpress_content_readback()`;
4. confirmar que os mesmos IDs aparecem no raw e no rendered, e que o hash de proveniência do raw confere.

Se não existir esse post ou se não houver uma instalação WordPress isolada com os filtros equivalentes, registrar a homologação de vídeo como **pendente**. O teste real #9894 não deve ser usado como substituto, pois não contém a marca nem os elementos de vídeo.

## Próximo passo operacional seguro

1. OpenCode deve copiar o plugin ativo para uma pasta temporária fora do document root, sem alterar o original.
2. Executar o \`README.md\` do patch kit: hashes originais, teste do helper, \`--dry-run\`, patch na cópia, \`php -l\`, testes e diff.
3. Se a cópia integral divergir das âncoras esperadas, parar e reconciliar a versão em vez de forçar o patch.
4. Disponibilizar uma instância WordPress de homologação isolada com o mesmo PHP, filtros e papel/capacidades para um teste controlado de persistência/readback. Sem ela, não declarar o teste de sanitização concluído.

**Nenhuma mudança da RC10.5 foi aplicada ao site ativo.** Sem merge, deploy, publicação, cron ou escrita em produção nesta etapa.
