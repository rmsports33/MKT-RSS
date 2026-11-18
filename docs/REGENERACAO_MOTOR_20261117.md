# Regeneração dos dois artigos pelo motor — 17/11/2026

Os rascunhos 9899 e 9900 foram **regerados pelo motor editorial** e substituídos.
Antes: texto escrito fora do motor, sem manifesto. Depois: pacote canônico com
12 módulos executados, hashes de versão e marca de proveniência no corpo.

| Post | `version_sha256` | `content_sha256` | Corpo no WP |
|---|---|---|---|
| 9899 | `73cf7c2140677b…` | `8ed81e545c867b…` | 7.259 bytes, marca presente, readback idêntico |
| 9900 | `34d79ca353fe4f…` | `d814a82573834d…` | 6.172 bytes, marca presente, readback idêntico |

O motor reportou `ENRIQUECIMENTO_PENDENTE`. Isso é honesto e correto:

- `editorial_voice_application = NOT_APPLIED` — não houve aplicação verificável
  do DNA, então não foi inventada prova;
- avaliação substantiva pendente;
- imagem/direitos pendentes.

Nenhum desses itens virou PASS. A marca apenas prova **de onde o texto veio**;
não aprova conteúdo nem substitui revisão humana.

## Verificação cruzada Python → PHP

Os corpos reais dos dois rascunhos foram lidos do WordPress e passados pela
função `cxgna_draft_readiness()` do plugin com a trava de proveniência:

```
real-9899.html: PASS | manifesto reconhecido pelo Gate
real-9900.html: PASS | manifesto reconhecido pelo Gate
```

Ou seja: o manifesto gerado pelo Python é aceito pela checagem em PHP do Gate.

## Observação de implantação

O checkout do servidor (`~/mkt-rss-runner`) estava em branch antiga; para esta
execução foram copiados `mkt_flow_p0/editorial_import.py` e
`mkt_flow_p0/editorial_provenance.py` da versão commitada localmente. O plugin
com a trava ainda **não foi implantado** no WordPress.
