# Ponte MKT-RSS → Conexo Editorial Gate v3

Estado: implementação isolada na branch \`feat/conexo-gate-v3-review-bridge-20261123\`. Não faz chamadas de rede, gravações WordPress/Turso, emissão de assinatura ou publicação. PR deve permanecer Draft até homologação do Gate e revisão independente.

## Objetivo

Conectar os contratos sem transformar o MKT-RSS em autoridade de aprovação:

1. MKT-RSS mantém o briefing de geração de seis campos já usado pela linha de runtime.
2. A ponte exige um perfil de persona explícito, separado, e produz o briefing \`conexo-editorial-brief/2\` de sete campos exigido pelo Gate.
3. O Revisor Único produz \`conexo-article-quality/2\`, com 16 dimensões, e falha fechado quando voz, persona ou imagens internas não têm evidência humana para o fingerprint exato.
4. O adaptador só monta uma requisição REST se o relatório do Revisor, o post lido em contexto edit e o snapshot persistido pelo Gate corresponderem.
5. O próprio Gate recalcula o preflight, verifica as 16 evidências humanas, associa a chave Ed25519 ao usuário WordPress autenticado e emite o Quality Record v3 assinado. Owner Approval e Owner Release continuam separados.

## Compatibilidade de briefing

O contrato canônico do MKT-RSS continua exatamente:

- \`genre\`
- \`reader\`
- \`need\`
- \`angle\`
- \`contribution\`
- \`limits\`

A ponte não altera o prompt de geração nem exige que o produtor invente a persona. O campo \`persona_profile\` é entrada explícita separada, com 20–1.200 caracteres. O adaptador constrói:

\`conexo-editorial-brief/2\` = briefing MKT de seis campos + \`persona\`.

A ausência de persona, qualquer campo extra no briefing legado ou divergência de hash interrompe a montagem da requisição.

## Contrato do Revisor Único

O novo método \`avaliar_artigo_gate_v3\` retorna as 16 dimensões requeridas pelo Gate:

\`versao\`, \`titulo\`, \`categoria\`, \`voz_editorial\`, \`persona\`, \`capa\`, \`imagens_internas\`, \`licenca_imagem\`, \`fontes\`, \`alegacoes\`, \`links_internos\`, \`seo\`, \`html\`, \`revisao_substantiva\`, \`visual_390\`, \`visual_1440\`.

A versão anterior do Revisor continua disponível para os consumidores legados. A função v2 acrescenta três requisitos humanos explícitos:
- \`voz_editorial\`: evidência humana no fingerprint atual e lente esperada determinada a partir do gênero/recorte;
- \`persona\`: perfil explícito e evidência humana para essa persona;
- \`imagens_internas\`: todas as tags IMG devem ter SRC e ALT; a ausência de imagem interna exige atestado humano explícito.

O relatório não é assinatura Ed25519, não certifica a identidade por si só, não prova fatos externos e não autoriza publicação. O rótulo do revisor e as evidências são diagnósticos auxiliares; a identidade operacional é verificada pelo usuário WordPress autenticado e pela chave pública registrada no Gate.

## Pré-condições da ponte

\`build_gate_quality_record_request\` requer:

- snapshot de Gate persistido, com UUID e hashes válidos nas versões de fingerprint/digest esperadas;
- leitura autenticada do post em contexto edit com \`content.raw\`, \`title.raw\` e \`excerpt.raw\`; strings achatadas ou somente \`rendered\` são rejeitadas;
- igualdade exata de post, tipo, status, slug, título, corpo, resumo, autor, data GMT, categorias, tags e capa entre a leitura WordPress e o snapshot;
- relatório do Revisor Único v2 para o mesmo post/fingerprint, com briefing, persona e lente correspondentes, timestamp válido e as 16 dimensões em VERIFICADO;
- chave do revisor que exista no Gate e esteja vinculada ao usuário WordPress autenticado;
- 16 grupos de evidência humana tipada, todos ligados ao mesmo fingerprint MKT, ao rótulo do revisor e ao snapshot Gate.

O adaptador também verifica que as referências citadas pelo Revisor aparecem nos respectivos grupos de evidência Gate. Capturas de 390/1440 exigem screenshot; capa exige o attachment da imagem destacada exata; evidências de imagem interna devem referenciar o snapshot ou attachment; referências de fontes/SEO aceitam URL HTTPS ou attachment.

## Funções públicas do adaptador

- \`normalize_gate_brief(legacy_brief, persona_profile=...)\`: tradução estrita para brief v2.
- \`gate_snapshot_fingerprint(snapshot)\` e \`gate_snapshot_digest(snapshot)\`: reproduzem o perfil determinístico do Gate, para verificação cruzada.
- \`validate_wordpress_post_matches_gate_snapshot(post, snapshot)\`: exige readback nativo e comparação integral.
- \`build_gate_assessment_request(...)\`: monta payload para \`POST /conexo/v2/quality-assessments\`.
- \`build_gate_quality_record_request(...)\`: monta payload para \`POST /conexo/v2/quality-records\`.

Essas funções apenas validam e montam dados. Não fazem HTTP, não leem WordPress, não fazem upload de evidências e não assinam. O chamador precisa obter os dados autenticados e anexar referências reais antes de usar o payload.

## Lacunas deliberadas antes da ativação

- O report Python do Revisor Único não é um atestado criptográfico. A prova assinada de aprovação é o Quality Record do Gate, emitido sob uma sessão WordPress autenticada e uma chave Ed25519 registrada. Uma próxima evolução poderá persistir o report bruto do Revisor em armazenamento de evidências e assinar seu hash como evidência associada.
- O adaptador não executa GET autenticado nem POST REST. A integração de runtime deve ser habilitada depois de confirmar os conectores de leitura \`context=edit\` e \`raw/rendered\` e uma revisão do endpoint real.
- O Gate precisa estar na versão que contém o Quality Record v3, briefing v2 e 16 checks; a branch de Gate PR #87 ainda deve passar novamente o CI no HEAD atual antes do consumo.
- Metadados SEO do plugin, direitos/licenças de imagem, pertinência de fontes e avaliação visual continuam dependentes de evidência humana e readback; o bridge não cria PASS automático.

## Validação isolada

O workflow direcionado executa apenas os testes do Revisor Único e da ponte, sem credenciais, WordPress ou serviços externos:

\`python -m pytest tests/test_revisor_qualidade_unico.py tests/test_conexo_gate_bridge.py -q\`.

Nenhum merge, deploy, ativação, cron, gravação WordPress/Turso ou publicação faz parte desta branch.
