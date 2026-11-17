# M07 — Fila de correção de rascunhos — 17/11/2026

**Somente leitura.** Nenhum rascunho foi alterado, aprovado ou publicado.
Ferramenta: `tools/wp_list_drafts_readonly.py`.

## O bloqueio não era senha: era escopo

A auditoria anterior dizia que faltava `WP_USER`/`WP_APP_PASSWORD`. O servidor
**tem** a credencial editorial (`WP_USER=Bot.editor` + `~/.config/conexo-os/wp-editorial.token`,
24 caracteres, senha de aplicativo). Ela é recusada nas rotas genéricas por
desenho:

```
GET /wp-json/wp/v2/posts?status=draft
-> HTTP 403 {"code":"cxrm_scope_denied",
             "message":"Credencial MKT-RSS limitada a correcao de rascunhos."}
```

Ou seja: a credencial é **intencionalmente estreita**. O caminho correto é a rota
oficial do plugin Conexo, que responde normalmente:

```
GET /wp-json/conexo/v1/editorial/remediation/queue
-> HTTP 200, schema conexo-remediation/1
```

Isso é proteção funcionando, não defeito.

## Resultado da fila

| Situação | Quantidade |
|---|---|
| Rascunhos na fila | **37** |
| Com correção automática possível (descrição SEO) | 34 |
| Exigem revisão humana de licença de imagem | **37 (todos)** |

Problemas mais frequentes:

| Problema | Ocorrências |
|---|---|
| Descrição SEO ausente ou curta | 34 |
| Legenda/crédito da imagem não documentado | 30 |
| Imagem sem texto alternativo descritivo | 30 |
| Capa genérica de RSS: verificar direitos e marca de terceiros | 30 |
| Origem/licença da imagem sem documentação auditável | 30 |
| Imagem destacada ausente ou inválida | 7 |
| Texto insuficiente para revisão completa | 1 |
| Fontes externas não vinculadas | 1 |

## O que isso significa

- **Nada aqui pode virar publicação.** Todos os 37 dependem de revisão humana de
  licença de imagem. Automação não resolve direito de imagem.
- **34 têm correção automática disponível** — mas é de metadado (descrição SEO
  extraída de parágrafo existente, sem validação factual). Corrigir exige
  `POST`, ou seja, **escrita no WordPress**. Não foi executado.
- O resto (legenda, alt, licença, capa) é trabalho humano de direção de arte e
  direitos, item por item.

## Achados colaterais

- Post `9633` com `modified_gmt = 0000-00-00`: data inválida no banco do WP.
  É um rascunho de teste (`[TESTE NAO PUBLICAR] M04.15.11E`).
- A fila inclui esse post de teste; ele não deveria estar no mesmo balde dos
  rascunhos reais.
- Rascunhos mais antigos são de **18/10** (título em inglês, texto insuficiente),
  o que indica pauta RSS capturada e nunca trabalhada.

## Próximo passo sugerido

1. Decidir o destino do post `9633` (rascunho de teste dentro da fila real).
2. Autorizar, ou não, a correção automática das 34 descrições SEO — é escrita em
   rascunho, reversível campo a campo, sem publicação.
3. Tratar licença de imagem dos 37 como frente separada (F1/F3), porque é o que
   realmente trava tudo.

## Como repetir

```
python tools/wp_list_drafts_readonly.py --saida fila_correcao.json
python tools/wp_list_drafts_readonly.py --json
```

No servidor a credencial é encontrada automaticamente em
`~/.config/conexo-os/wp-editorial.token`; fora dele, usar
`~/.config/conexo-os/wp-reader.env` com `WP_URL`, `WP_USER`, `WP_APP_PASSWORD`.
