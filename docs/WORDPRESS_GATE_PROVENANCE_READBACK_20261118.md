# Proveniência no Gate WordPress e homologação de readback — 18/11/2026

## Estado desta entrega

O lado MKT-RSS recebeu uma camada fail-closed adicional:
- \`mkt_flow_p0.editorial_provenance.validar_integridade()\` verifica unicidade, estrutura tipada e hash do corpo.
- \`mkt_flow_p0.editorial_provenance.validar()\` também exige módulos executados, aplicação da voz, revisão substantiva PASS e direitos de imagem booleanos confirmados.
- \`editorial_publish_gate.authorize_publish()\` passou a rejeitar ausência de \`content.raw\` e qualquer marca ausente, inválida ou com estado editorial pendente. A marca não substitui \`owner_release\`, pacote canônico ou revisão factual confiável.
- \`editorial_wordpress_adapter.validate_wordpress_content_readback()\` é uma verificação local/read-only: confere integridade do corpo bruto e, quando há vídeo, compara iframe e VideoObject entre \`content.raw\` e \`content.rendered\`.
- O importador agora informa \`INSERIDO_AGUARDANDO_REVISAO_HUMANA\`; metadados válidos do vídeo não são tratados como curadoria humana.
- \`media_rights_confirmed\` exige booleano real. A string \`"false"\` não pode virar confirmação por coerção.

**Isso ainda não prova que o Gate PHP instalado em conexotech.com.br consome a marca.** O código do plugin que implementa as funções centrais \`cxeg_*\` não foi localizado na árvore versionada de \`rmsports33/-site-conexotech\`. O plugin versionado de publicação imediata apenas delega a funções do Gate existente; não é seguro colocar a regra somente nessa interface. Não alterar esse wrapper nem criar um segundo Gate.

## Contrato da marca

O corpo contém exatamente um comentário:
\`<!-- cxeg-package:v1:{JSON} -->\`

Campos JSON obrigatórios e exclusivos:
- \`content_sha256\`: SHA-256 do corpo sem a marca.
- \`version_sha256\`: SHA-256 hexadecimal da versão de handoff.
- \`modules\`: mapa dos módulos obrigatórios para \`EXECUTED\` (estados conhecidos: \`EXECUTED\`, \`SKIPPED\`, \`FAILED\`).
- \`voice_status\`: \`PROMPT_APPLIED\`, \`HUMAN_ADAPTED\`, \`ASSISTED_ADAPTED\` ou \`NOT_APPLIED\`.
- \`substance_status\`: \`PASS\`, \`PENDING\` ou \`FAIL\`.
- \`image_rights_confirmed\`: JSON booleano real.

Módulos exigidos: \`editorial_identity\`, \`editorial_core_offline\`, \`seo\`, \`editorial_readiness\`, \`editorial_substance\`.

Canonicalização do hash em todas as linguagens: remover somente a marca identificada e aplicar trim apenas dos caracteres ASCII espaço, tab, CR e LF no final (\`rstrip(" \\t\\r\\n")\` em Python; \`rtrim($body, " \\t\\n\\r")\` em PHP); calcular SHA-256 UTF-8. Não normalizar HTML, Unicode, atributos, ordem de atributos nem espaços internos.

A marca é um **recibo de integridade**, não uma assinatura. Ela não autentica identidade humana, execução real de módulo ou licença de mídia. O Gate deve exigir separadamente sua aprovação humana autenticada e seus demais contratos.

## Integração obrigatória no Gate PHP

Quando o código-fonte oficial do plugin Gate for localizado, integrar o validador no ponto central compartilhado por todas as rotas de aprovação/transição, antes de emitir owner release ou mudar estado. Não integrar só na tela administrativa nem só no plugin de agenda/publicação imediata.

Requisitos do consumidor PHP:
1. Obter o post persistido do banco/ snapshot confiável do próprio Gate. Não usar \`content.rendered\`, POST do formulário, campo trazido pelo cliente ou hash colado.
2. Rejeitar \`post_content\` ausente ou não textual.
3. Contar ocorrências de \`cxeg-package\\s*:\` sem diferenciar caixa; exigir exatamente uma. Qualquer segunda ocorrência ou marca quebrada reprova.
4. Exigir exatamente um comentário completo \`<!-- cxeg-package:v1:{...} -->\`; decodificar JSON com exceção em erro.
5. Exigir o conjunto exato de seis campos, tipos estritos, SHA-256 hexadecimal e estados conhecidos.
6. Remover somente a marca completa, calcular SHA-256 conforme a canonicalização acima e comparar com \`hash_equals\`.
7. Exigir os cinco módulos em \`EXECUTED\`, voz diferente de \`NOT_APPLIED\`, substância \`PASS\` e \`image_rights_confirmed === true\`.
8. Se qualquer verificação falhar, manter o Gate em bloqueio; não emitir \`owner_release\`, não aceitar e não publicar.
9. Mesmo com a marca válida, continuar exigindo identidade autorizada do proprietário, checks completos, revisão factual e vínculo à versão exata. Não converter hash de conteúdo em aprovação.

O código PHP exato não foi inserido neste repositório porque o plugin que define e assina o Gate não está versionado aqui. Implementar um consumidor em plugin auxiliar não garantiria cobertura de todas as rotas e criaria falsa segurança.

## Testes obrigatórios do consumidor PHP

Criar testes no repositório/plug-in oficial do Gate para:
- corpo sem marca;
- JSON inválido ou campos ausentes/extras;
- SHA incorreto e alteração de um byte do corpo;
- marcas duplicadas idênticas, conflitantes e malformadas;
- módulo ausente ou diferente de \`EXECUTED\`;
- voz \`NOT_APPLIED\`, substância \`PENDING/FAIL\`, direitos \`false\` ou string;
- marca estruturalmente válida, seguida ainda dos checks e owner release normais;
- conteúdo alterado entre leitura e emissão do owner release.

Os casos negativos devem provar que nenhuma rota de aceite consegue ignorar o validador. O teste positivo só prova que a marca passou; não deve publicar nem criar aceite real.

## Readback WordPress

A implementação Python faz verificação read-only sobre um objeto REST já obtido. Para prova real do comportamento de WordPress são necessários:
- \`content.raw\` obtido em contexto de edição pelo papel de serviço autorizado;
- \`content.rendered\` retornado na mesma leitura;
- mesma versão do Gate, WordPress, filtros e papel/capacidades usados operacionalmente;
- um rascunho de teste descartável em ambiente isolado, nunca um post público.

Critérios: o hash do corpo raw deve corresponder; se o raw contém vídeo, o rendered deve conservar o iframe \`youtube-nocookie\` e o JSON-LD \`VideoObject\` com o mesmo ID. Remoção/sanitização de qualquer um deles reprova a homologação. Se raw ou rendered não puderem ser lidos, resultado é inconclusivo/bloqueado.

**Não executar POST/PUT em produção para esse teste.** O staging do projeto foi removido e nenhum ambiente WordPress isolado foi disponibilizado nesta tarefa. Não criar rascunho, usuário, token, cron ou staging sem autorização específica.

## Próximos insumos necessários

1. Caminho e versão/commit do plugin PHP oficial que define \`cxeg_snapshot\`, \`cxeg_owner_approve\`, \`cxeg_owner_release_read\` e a transição central do Gate.
2. Checkout/cópia isolada desse plugin para implementação/testes do consumidor PHP.
3. Ambiente WordPress isolado com o mesmo papel/capacidades para o teste de gravação/readback.

Até esses insumos existirem, MKT-RSS bloqueia localmente conteúdo sem proveniência válida, mas a integração do Gate PHP e a persistência real do WordPress permanecem **não homologadas**.
