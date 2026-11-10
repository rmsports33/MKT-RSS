# Gate editorial unificado — aplicação da identidade e prontidão

Data: 10/11/2026

## Regra operacional

Toda entrada editorial usa a prontidão comum do MKT-RSS: geração RSS, artigo importado de editor humano ou de outro provedor. Nenhuma rota pode inferir que a voz foi aplicada apenas porque os metadados identificam ConexoTech ou Conexo Insight.

## Evidência da voz

- O caminho de geração MKT-RSS grava `editorial_voice_application.status=PROMPT_APPLIED`, o hash do DNA editorial e o hash da chamada completa enviada ao provedor.
- O importador de texto pronto, que não chama provedor, registra `NOT_APPLIED` por padrão. A prontidão inclui `persona_editorial_nao_aplicada` até que uma etapa de adaptação com evidência seja concluída.
- `PROMPT_APPLIED` prova que a instrução de DNA integrou a geração. Não certifica qualidade literária, factualidade ou aprovação humana; a revisão de voz continua registrada separadamente.

## Manifesto e versão

Cada pacote importado registra:
- lista dos módulos executados;
- manifesto com estado `EXECUTED` separado de `PASS` ou prontidão;
- status de conclusão derivado da prontidão editorial;
- indicador `article_complete_for_human_review`;
- hash do conteúdo e da versão.

A lista de módulos executados não significa que todos passaram. Pendências de fonte, voz, imagem, links, SEO ou contrato factual continuam explícitas. Qualquer alteração de texto cria nova versão; recibos de uma versão anterior não autorizam apresentar a versão editada como processada.

## Rotas e limites

RSS e importação já usam o mesmo módulo `editorial_readiness`; este gate adiciona evidência da persona a essa decisão comum. O importador offline continua sem IA, rede ou escrita no WordPress. Uma importação sem prova da voz permanece pendente em vez de receber aprovação inventada. O caminho de geração registra a aplicação do prompt compartilhado; a adequação efetiva ainda é objeto da avaliação editorial humana.

Rascunho remoto, revisão humana e autorização para publicação continuam estados separados. Este gate não publica nem altera a política de autorização.
