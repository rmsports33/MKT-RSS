# Revisão de integração — PR #127 (18/11/2026)

## Decisão

**Compatibilidade de Git/base: aprovada. Integração funcional ponta a ponta: bloqueada. Não promover para ready nem mesclar nesta etapa.**

A revisão não encontrou conflito de ancestralidade nem sobreposição direta com as mudanças posteriores já incorporadas à base. Foram identificadas lacunas na aplicação efetiva da nova marca de proveniência pelo Gate e na semântica do estado de curadoria de vídeo. A validação WordPress de persistência do HTML também não foi demonstrada.

## Identificação e estado

- Repositório: `rmsports33/MKT-RSS`
- PR: #127 — `fix/editorial-import-provenance-video-20261118`
- Base verificada: `feat/hostinger-runtime-independente-20261113`, SHA `3901ca0802d500381d7b0372b4d75dc6fc2ec40e`
- SHA de código/testes validado pelo OpenCode: `67116a57e4e00561574ea398e6ff7b3976281275`
- HEAD documental antes desta revisão: `afee368ffa6ab31bc9e4222c4f37aefd619690bf`
- Comparação GitHub base...HEAD: 14 commits à frente, 0 atrás; estado `ahead`.
- O GitHub informou `mergeable=true` para o PR. Isso indica ausência de conflito automático detectado, não aprovação funcional.
- Os commits adicionados durante esta revisão são documentais/limpeza; nenhum arquivo de runtime ou teste foi alterado após a execução de testes no SHA `67116a5`.

## Compatibilidade com mudanças posteriores

A branch-base atual é exatamente `3901ca0`. Os trabalhos já incorporados estão presentes nessa base:

| Trabalho | Arquivos | Conferência |
| --- | --- | --- |
| PR #125 — normalização de títulos REST do Gate | `mkt_flow_p0/editorial_correction_queue.py`, `tests/test_editorial_correction_queue.py` | Os SHA dos blobs na base `3901ca0` são idênticos aos blobs do HEAD validado do PR #125. |
| PR #126 — quebras de linha do Gemini | `mkt_flow_p0/ai_providers.py`, `tests/test_ai_providers.py` | Os SHA dos blobs na base `3901ca0` são idênticos aos blobs do HEAD validado do PR #126. |
| PR #128 — política de consolidação contínua | `AGENTS.md`, `docs/CONSOLIDACAO_FACTUAL_20261118.md`, `docs/POLITICA_CONSOLIDACAO_CONTINUA.md` | PR paralelo, documental, sem arquivos em comum com o #127. |

Nenhum desses seis caminhos de PRs #125/#126/#128 se sobrepõe aos arquivos de runtime ou testes do #127. O PR #124 continua divergente e em rascunho; não foi usado como fonte de código nem incorporado. O PR #122 está supersedido; a correção posterior do Gemini já está na base via #126.

## Revisão do diff do PR #127

- `mkt_flow_p0/editorial_core_offline.py`: introduz `montar_documento_preview(article, fragmento)` e mantém a assinatura pública de `gerar_html(article, markdown)`, que delega ao helper. Não foi encontrada quebra de chamada existente no diff.
- `mkt_flow_p0/editorial_import.py`: amplia os campos admitidos para vídeo, valida a entrada antes de criar artefatos, mantém a importação sem escrita WordPress, faz a CLI começar offline e exige `--online` explícito para desenvolvimento com provedor. O corpo de vídeo é montado antes da prontidão e do preflight SEO; prévia e corpo recebem o mesmo fragmento. A assinatura de `processar_artigo_importado` foi preservada.
- `mkt_flow_p0/editorial_video.py`: aceita os formatos documentados, rejeita origem ambígua e campos desconhecidos, escapa texto HTML e neutraliza caracteres que poderiam encerrar o bloco JSON-LD. O ID do iframe é restrito ao alfabeto/tamanho esperado.
- `mkt_flow_p0/editorial_provenance.py`: adiciona marca com hash de conteúdo/versão e manifesto de módulos/estados. A integridade local é testada, mas a ligação dessa marca à autorização do Gate não está demonstrada (ver achado 1).
- Testes: os dois testes de regressão de tabela agora aceitam atributos em `<table>` e mantêm as verificações de conteúdo. As novas suítes cobrem proveniência, formatos de vídeo, importação e sincronismo prévia/corpo.
- Documentação: o relatório final registra os resultados de execução. O relatório histórico anterior estava com caracteres corrompidos e contradizia a validação final; foi reescrito como histórico substituído. O arquivo `.gitattributes` adicionado sem qualquer atributo efetivo foi removido.

## Achados

### 1. Bloqueador — consumo da marca pelo Gate não comprovado

O importador chama `editorial_provenance.marcar()` para inserir a marca; não chama `editorial_provenance.validar()`. No código MKT-RSS da base, o autorizador existente `editorial_publish_gate.authorize_publish()` exige recibo de proprietário e pacote editorial canônico, mas não integra o novo validador. O módulo `gate_unified.py` também não referencia a nova marca.

A inspeção da árvore versionada de `rmsports33/-site-conexotech` encontrou o plugin de agenda/publicação imediata, que delega ao Gate por funções `cxeg_*`, mas não encontrou implementação versionada que consuma `cxeg-package:v1`. A busca pelo identificador da marca no repositório também não retornou implementação correspondente. Isso **não prova que o código não exista no servidor WordPress**; significa que a integração efetiva do lado do Gate não pode ser certificada a partir dos repositórios inspecionados.

Além disso, `editorial_provenance.validar()` ainda não impõe integralmente um contrato estrito ao manifesto: rejeita `voice_status=NOT_APPLIED`, mas não limita o valor a estados conhecidos; usa avaliação por truthiness para `image_rights_confirmed`; não valida o tipo do mapa `modules` antes de chamar `.get()`; e não valida o formato de `version_sha256`. Como a marca é um JSON com hash, não uma assinatura, ela demonstra consistência do corpo, mas não autentica por si só quem executou módulos ou confirmou direitos.

**Consequência:** não afirmar que o Gate já bloqueia rascunhos sem a marca, nem tratar a marca como aprovação ou prova criptográfica. Para encerrar este achado é necessário localizar/validar o consumidor real no Gate WordPress, exigir contrato estrito e cobrir o comportamento com testes do lado do consumidor. Se esse consumidor estiver fora do repositório, registrar a versão/commit exatos e a evidência de validação sem alterar produção.

### 2. Importante — estado de curadoria de vídeo afirma mais do que a entrada prova

Em `editorial_import.py`, a presença de campos válidos faz o relatório gravar `video_review.status=INSERIDO_COM_CURADORIA_HUMANA`. Não há no payload um atestado explícito, vinculado à versão, que comprove a verificação dos critérios da política de vídeo (canal, uso real do aparelho, ausência de jabá/clickbait e permissão de incorporação). Os pontos são opcionais e o código não comprova que o vídeo foi assistido.

A inserção não libera publicação — `human_acceptance` continua `PENDING` e `publication_authorized=false` —, mas o estado do relatório pode induzir o operador a entender que a curadoria já ocorreu.

**Ajuste recomendado:** renomear o estado para algo como `INSERIDO_AGUARDANDO_REVISAO_HUMANA`, ou exigir um atestado explícito/versionado antes de registrar curadoria confirmada. Atualizar o teste que hoje espera o estado afirmativo.

### 3. Pendente de homologação — HTML persistido no WordPress

A suíte local verifica o HTML gerado e a presença de iframe/JSON-LD na prévia e no corpo. Não existe nesta evidência um ciclo de escrita/readback WordPress para comprovar que o papel usado pelo importador preserva `<iframe>` e `<script type="application/ld+json">` após os filtros/capacidades do WordPress. O PR não executa escrita WordPress e isso foi correto; portanto a persistência desses elementos continua não homologada.

**Ajuste recomendado:** antes de declarar integração WordPress concluída, validar o corpo em ambiente isolado/controlado com o mesmo papel/capacidades e fazer readback, sem publicar e sem escrever em produção durante esta revisão.

## Testes e evidências

Execução reportada pelo OpenCode em checkout isolado `/home/u401421381/mkt-rss-pr127-67116a5`:

- SHA: `67116a57e4e00561574ea398e6ff7b3976281275`
- Python: 3.11.18
- Teste Android Drop: 1 passed.
- Teste de fluxo editorial/importação: 1 passed.
- Quatro módulos focados: 120 passed.
- Bateria relevante: 288 passed, 0 failed, 10 subtests.

Registro: https://github.com/rmsports33/MKT-RSS/pull/127#issuecomment-6986915272
Relatório final: [VALIDACAO_FINAL_PR127_20261118.md](VALIDACAO_FINAL_PR127_20261118.md)

Os resultados são evidência de testes no SHA `67116a5`. Os commits posteriores desta revisão são somente documentação/limpeza e não alteram código/testes.

## Conclusão operacional

- Compatibilidade de Git/base: **aprovada**.
- Conflitos com PRs #125 e #126 já incorporados: **não encontrados**.
- Sobreposição com PR #128: **não encontrada**.
- Regressões locais reportadas: **288 passed, 0 failed**.
- Integração real do novo manifesto com o Gate WordPress: **não comprovada**.
- Curadoria humana de vídeo: **estado reportado sem atestado explícito**.
- Persistência de iframe/JSON-LD no WordPress: **não homologada**.

**Decisão: manter o PR #127 em draft e não mesclar por enquanto.** A ausência de conflito Git não elimina os três itens de integração acima. Nenhuma produção, WordPress, Turso, Gate, cron, deploy ou publicação foi alterada nesta revisão.
