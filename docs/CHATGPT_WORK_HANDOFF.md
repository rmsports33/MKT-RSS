# ChatGPT Work / Codex — troca supervisionada de evidências

Objetivo: produzir **prévia editorial** pelo ChatGPT Work ou Codex usando apenas as evidências coletadas pelo MKT-RSS, sem API paga, sem autenticação automatizada na conta ChatGPT e **sem WordPress**.

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
