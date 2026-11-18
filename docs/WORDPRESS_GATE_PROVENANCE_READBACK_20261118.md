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
- **14 casos contratuais** passaram no helper isolado.
- \`php -l\` passou para o helper.
- O aplicador foi exercitado em fixture sintético com as âncoras necessárias: dry-run, aplicação, lint do núcleo/publisher sintéticos e repetição dos 14 casos passaram.

Isso não é teste da cópia integral do plugin RC10.4 nem homologação na instalação ativa. A aplicação na cópia completa ainda deve ser feita pelo OpenCode, conforme o README do patch kit, e os resultados precisam ser registrados com SHA-256, PHP, saída de lint, testes e diff.

## Readback WordPress

A camada MKT-RSS disponibiliza \`validate_wordpress_content_readback()\`, que verifica:
- integridade do \`content.raw\`;
- presença de um iframe \`youtube-nocookie\` e de \`VideoObject\` JSON-LD com o mesmo ID no raw;
- preservação correspondente em \`content.rendered\`.

O WordPress connector em contexto edit para os posts consultados retornou \`content\` como string, sem separar os campos raw/rendered. Portanto essa consulta não satisfaz o contrato de readback para testar a sanitização do iframe e JSON-LD.

O staging foi removido do projeto. Não foi criado rascunho de teste nem executado POST/PUT em produção. A persistência dos elementos de vídeo segue **não homologada**.

## Próximo passo operacional seguro

1. OpenCode deve copiar o plugin ativo para uma pasta temporária fora do document root, sem alterar o original.
2. Executar o \`README.md\` do patch kit: hashes originais, teste do helper, \`--dry-run\`, patch na cópia, \`php -l\`, testes e diff.
3. Se a cópia integral divergir das âncoras esperadas, parar e reconciliar a versão em vez de forçar o patch.
4. Disponibilizar uma instância WordPress de homologação isolada com o mesmo PHP, filtros e papel/capacidades para um teste controlado de persistência/readback. Sem ela, não declarar o teste de sanitização concluído.

**Nenhuma mudança da RC10.5 foi aplicada ao site ativo.** Sem merge, deploy, publicação, cron ou escrita em produção nesta etapa.
