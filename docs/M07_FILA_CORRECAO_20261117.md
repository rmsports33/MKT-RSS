<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# M07 â€” Fila de correÃ§Ã£o de rascunhos â€” 17/11/2026

**Somente leitura.** Nenhum rascunho foi alterado, aprovado ou publicado.
Ferramenta: `tools/wp_list_drafts_readonly.py`.

## O bloqueio nÃ£o era senha: era escopo

A auditoria anterior dizia que faltava `WP_USER`/`WP_APP_PASSWORD`. O servidor
**tem** a credencial editorial (`WP_USER=Bot.editor` + `~/.config/conexo-os/wp-editorial.token`,
24 caracteres, senha de aplicativo). Ela Ã© recusada nas rotas genÃ©ricas por
desenho:

```
GET /wp-json/wp/v2/posts?status=draft
-> HTTP 403 {"code":"cxrm_scope_denied",
             "message":"Credencial MKT-RSS limitada a correcao de rascunhos."}
```

Ou seja: a credencial Ã© **intencionalmente estreita**. O caminho correto Ã© a rota
oficial do plugin Conexo, que responde normalmente:

```
GET /wp-json/conexo/v1/editorial/remediation/queue
-> HTTP 200, schema conexo-remediation/1
```

Isso Ã© proteÃ§Ã£o funcionando, nÃ£o defeito.

## Resultado da fila

| SituaÃ§Ã£o | Quantidade |
|---|---|
| Rascunhos na fila | **37** |
| Com correÃ§Ã£o automÃ¡tica possÃ­vel (descriÃ§Ã£o SEO) | 34 |
| Exigem revisÃ£o humana de licenÃ§a de imagem | **37 (todos)** |

Problemas mais frequentes:

| Problema | OcorrÃªncias |
|---|---|
| DescriÃ§Ã£o SEO ausente ou curta | 34 |
| Legenda/crÃ©dito da imagem nÃ£o documentado | 30 |
| Imagem sem texto alternativo descritivo | 30 |
| Capa genÃ©rica de RSS: verificar direitos e marca de terceiros | 30 |
| Origem/licenÃ§a da imagem sem documentaÃ§Ã£o auditÃ¡vel | 30 |
| Imagem destacada ausente ou invÃ¡lida | 7 |
| Texto insuficiente para revisÃ£o completa | 1 |
| Fontes externas nÃ£o vinculadas | 1 |

## O que isso significa

- **Nada aqui pode virar publicaÃ§Ã£o.** Todos os 37 dependem de revisÃ£o humana de
  licenÃ§a de imagem. AutomaÃ§Ã£o nÃ£o resolve direito de imagem.
- **34 tÃªm correÃ§Ã£o automÃ¡tica disponÃ­vel** â€” mas Ã© de metadado (descriÃ§Ã£o SEO
  extraÃ­da de parÃ¡grafo existente, sem validaÃ§Ã£o factual). Corrigir exige
  `POST`, ou seja, **escrita no WordPress**. NÃ£o foi executado.
- O resto (legenda, alt, licenÃ§a, capa) Ã© trabalho humano de direÃ§Ã£o de arte e
  direitos, item por item.

## Achados colaterais

- Post `9633` com `modified_gmt = 0000-00-00`: data invÃ¡lida no banco do WP.
  Ã‰ um rascunho de teste (`[TESTE NAO PUBLICAR] M04.15.11E`).
- A fila inclui esse post de teste; ele nÃ£o deveria estar no mesmo balde dos
  rascunhos reais.
- Rascunhos mais antigos sÃ£o de **18/10** (tÃ­tulo em inglÃªs, texto insuficiente),
  o que indica pauta RSS capturada e nunca trabalhada.

## PrÃ³ximo passo sugerido

1. Decidir o destino do post `9633` (rascunho de teste dentro da fila real).
2. Autorizar, ou nÃ£o, a correÃ§Ã£o automÃ¡tica das 34 descriÃ§Ãµes SEO â€” Ã© escrita em
   rascunho, reversÃ­vel campo a campo, sem publicaÃ§Ã£o.
3. Tratar licenÃ§a de imagem dos 37 como frente separada (F1/F3), porque Ã© o que
   realmente trava tudo.

## Como repetir

```
python tools/wp_list_drafts_readonly.py --saida fila_correcao.json
python tools/wp_list_drafts_readonly.py --json
```

No servidor a credencial Ã© encontrada automaticamente em
`~/.config/conexo-os/wp-editorial.token`; fora dele, usar
`~/.config/conexo-os/wp-reader.env` com `WP_URL`, `WP_USER`, `WP_APP_PASSWORD`.
