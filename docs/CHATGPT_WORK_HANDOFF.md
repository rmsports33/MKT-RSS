# ChatGPT Work / Codex — troca supervisionada de evidências

Objetivo: produzir **prévia editorial** pelo ChatGPT Work ou Codex usando apenas as evidências coletadas pelo MKT-RSS, sem API paga, sem autenticação automatizada na conta ChatGPT e **sem WordPress**.

## Revisão de qualidade editorial (DNA oficial Conexo OS)

A fonte normativa é [`rmsports33/conexo-os/docs/EDITORIAL_DNA_V1.md`](https://github.com/rmsports33/conexo-os/blob/main/docs/EDITORIAL_DNA_V1.md), indicada também pelos arquivos `AGENTS.md` do núcleo e do bot-redator. **Não criar uma segunda política editorial no MKT-RSS.**

O pacote e o comando `review` conferem lastro, estrutura e rastreabilidade; **não certificam qualidade de matéria jornalística**. Antes de apresentar qualquer resultado como *artigo pronto para aprovação*:

1. Identificar o gênero: notícia, guia, review ou comparativo; aplicar estrutura e comprimento proporcionais à pauta e à evidência.
2. Avaliar separadamente **factualidade**, **forma**, **substância**, **elegância**, **SEO honesto**, **atribuição**, **direitos** e **disclosure**, conforme o DNA oficial.
3. Para notícia, exigir contexto, relevância e utilidade verificável para o leitor, narrativa coesa e transições; cinco claims rastreadas não equivalem automaticamente a cinco parágrafos publicáveis.
4. Se houver apenas claims e notas curtas, nomear **resumo de evidências** ou **rascunho editorial** — nunca *artigo pronto*. Sem contribuição verificável, optar por digest ou não produzir artigo.
5. Distinguir o parecer editorial assistido do aceite humano: até aceite específico, estado `REVISAO_EDITORIAL_PENDENTE` e `REVISAO_SEMANTICA_PENDENTE`. Nenhum dos dois libera o WordPress, mesmo com CI verde.

**Falha identificada no piloto Android (26/10/2026):** a prévia `docs/previews/android_drop_final_human_review_20261026.md` sintetizou cinco claims em parágrafos telegráficos e foi indevidamente tratada como prévia final. O responsável solicitou reescrita em formato de artigo. Preservar a captura original; reescrever a prévia sem acrescentar fatos não documentados, antes de pedir nova revisão editorial humana.

Este procedimento é **uma checagem humana/documental**, não um gate de execução automática. Alterações nos prompts ou gates executáveis exigem tarefa separada, avaliação de impacto e testes proporcionais. Não altera `acao=bloqueado`, `escreveu=false`, nem autorizações de merge, deploy, custo ou publicação.

## Exportação (Python 3.12, stdlib + código existente)

Após um revisor obter e aprovar o contrato EditorialContract 1.0 e capturas autênticas (não usar os fixtures de teste como fontes reais):

```sh
python -m mkt_flow_p0.chatgpt_work_handoff export --contract contrato.json --captures capturas.json --output pacote-work.json
```

Revise o pacote (ele contém conteúdo que será enviado ao ChatGPT). Em uma tarefa supervisionada no ChatGPT Work ou Codex, forneça `pacote-work.json` como entrada e peça a execução das instruções `instructions` sem consultas externas ou escrita em WordPress. Salve a resposta exclusivamente como `resposta.json` com `{"texto_markdown":"...", "referencias_traducao":{"frase em português normalizada": ["id_da_claim_original"]}}`. **Não há conector bidirecional automático nem job de Work criado por este código.**

```sh
python -m mkt_flow_p0.chatgpt_work_handoff review --package pacote-work.json --response resposta.json --output revisao.json
```

Inspecione `revisao.json`. O status é **sempre bloqueado**, inclusive se cobertura literal for constatada; não é certificação semântica ou de procedência. Para uma futura publicação, são necessários auditoria factual independente, revisão humana e autorização explícita. O formato exportado usa SHA-256 para detectar adulteração casual, não assinatura de origem confiável.

**Custos:** não fornece ou usa `OPENAI_API_KEY`, `GROQ_API_KEY` nem outros tokens. O ChatGPT é usado dentro das funcionalidades/limites da conta, mediante ação do usuário; não pressupõe acesso programático.

## Tradução e paráfrase

Quando o artigo estiver em português e a fonte estiver em inglês, use `referencias_traducao` para indicar, por frase normalizada (minúsculas e espaços simples), os IDs das claims originais que sustentariam a tradução. **Essas referências não constituem verificação semântica.** O resultado `REVISAO_SEMANTICA_PENDENTE` somente organiza as frases para um revisor humano; o estado externo continua `acao=bloqueado`, `escreveu=false` e `verificacao_factual=NAO_VERIFICADO`. IDs inexistentes ou frases sem correspondência permanecem `BLOQUEADO`. Não equiparar esse mapeamento à autenticação da fonte ou autorização de publicação.

## Capturas completas obrigatórias na exportação CLI

Antes do export, gere as capturas a partir do corpo integral da fonte com `mkt_flow_p0.captura_completa.criar_captura_completa(url, texto, titulo=...)` e salve um dicionário `source_id -> captura` em `capturas.json`. A exportação por linha de comando agora **rejeita** capturas curtas (menos de 100 palavras), sem metadados, com hash do corpo divergente ou cujas IDs não coincidam com as fontes do contrato. Isso evita reutilizar o ensaio Android anterior, que preservava apenas uma frase. O corpo completo é mantido sem cortes e com SHA-256 por fonte, além do digest SHA-256 do pacote.

O mínimo de 100 palavras é apenas um critério técnico de completude aproximada, **não certificação da fonte**. Antes de aprovar claims, um revisor independente deve conferir URL, origem, integridade, data e conteúdo de cada captura. O indicador `status_revisao: PENDENTE` nunca se transforma automaticamente em PASS. Não use trechos fabricados ou fixtures como capturas reais.
