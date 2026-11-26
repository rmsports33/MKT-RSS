<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# RegeneraÃ§Ã£o dos dois artigos pelo motor â€” 17/11/2026

Os rascunhos 9899 e 9900 foram **regerados pelo motor editorial** e substituÃ­dos.
Antes: texto escrito fora do motor, sem manifesto. Depois: pacote canÃ´nico com
12 mÃ³dulos executados, hashes de versÃ£o e marca de proveniÃªncia no corpo.

| Post | `version_sha256` | `content_sha256` | Corpo no WP |
|---|---|---|---|
| 9899 | `73cf7c2140677bâ€¦` | `8ed81e545c867bâ€¦` | 7.259 bytes, marca presente, readback idÃªntico |
| 9900 | `34d79ca353fe4fâ€¦` | `d814a82573834dâ€¦` | 6.172 bytes, marca presente, readback idÃªntico |

O motor reportou `ENRIQUECIMENTO_PENDENTE`. Isso Ã© honesto e correto:

- `editorial_voice_application = NOT_APPLIED` â€” nÃ£o houve aplicaÃ§Ã£o verificÃ¡vel
  do DNA, entÃ£o nÃ£o foi inventada prova;
- avaliaÃ§Ã£o substantiva pendente;
- imagem/direitos pendentes.

Nenhum desses itens virou PASS. A marca apenas prova **de onde o texto veio**;
nÃ£o aprova conteÃºdo nem substitui revisÃ£o humana.

## VerificaÃ§Ã£o cruzada Python â†’ PHP

Os corpos reais dos dois rascunhos foram lidos do WordPress e passados pela
funÃ§Ã£o `cxgna_draft_readiness()` do plugin com a trava de proveniÃªncia:

```
real-9899.html: PASS | manifesto reconhecido pelo Gate
real-9900.html: PASS | manifesto reconhecido pelo Gate
```

Ou seja: o manifesto gerado pelo Python Ã© aceito pela checagem em PHP do Gate.

## Troca de pauta em 18/11

A pedido do proprietÃ¡rio, o artigo do Senado foi **excluÃ­do**: post 9899 movido
para a lixeira (`DELETE` autenticado, readback `status=trash`). O tema era de
governo, fora do nicho de produtos do site.

Nova pauta escolhida entre as jÃ¡ descobertas: **"Melhor TV 65 polegadas"**
(`29edd1e84516adfe4b0b804862ed06da`), marcada como `SELECIONADA` na fila com
auditoria (`DESCOBERTA â†’ SELECIONADA`, evento `29edd1e8â€¦`).

O guia foi gerado pelo motor com o pacote canÃ´nico:

| Post | TÃ­tulo | VersÃ£o | Marca |
|---|---|---|---|
| **9906** | Melhor TV 65 polegadas em 2026: 13 modelos e como escolher sem erro | `3a176643f31633c7â€¦` | presente, hash local = hash no WP |

Status do motor: `ENRIQUECIMENTO_PENDENTE` â€” voz `NOT_APPLIED`, avaliaÃ§Ã£o
substantiva `PENDING`, imagem/direitos pendentes. Nada virou PASS.

O guia nÃ£o repete preÃ§os: eles envelhecem e exigem data de captura. As
especificaÃ§Ãµes sÃ£o atribuÃ­das ao Tecnoblog e aos fabricantes; nenhum teste
prÃ³prio foi inventado.


O checkout do servidor (`~/mkt-rss-runner`) estava em branch antiga; para esta
execuÃ§Ã£o foram copiados `mkt_flow_p0/editorial_import.py` e
`mkt_flow_p0/editorial_provenance.py` da versÃ£o commitada localmente. O plugin
com a trava ainda **nÃ£o foi implantado** no WordPress.
