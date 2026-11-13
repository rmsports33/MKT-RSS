# Auditoria de mídia — 2026-11-13 — #9705 e fila WordPress

## Alterações verificadas ao vivo
- Rascunho #9705: mídia de origem #9704 (`featured-60.jpg`, sem crédito/alt e com branding 9to5Google visível na captura) desvinculada.
- Nova mídia #9888: foto Fitbit Inspire 3, autor Tatsuo Yamashita, Wikimedia Commons (página File:Fitbit_inspire_3_(55322650282).jpg), CC BY 4.0. Registro do WordPress inclui autor, fonte, licença, legenda e alt. Associada ao rascunho #9705, estado continua `draft`.
- Gate rc10.4 foi instalado e confirmado ativo pelo inventário de plugins; o painel coloca #9705 na fila de revisão humana sem pendências **técnicas**. Isso não equivale a parecer factual ou aprovação.
- 11 arquivos PHP sem erro de sintaxe; 10 cenários locais de decisão de metadados passaram. Esses testes não simulam detecção visual real de marcas nos pixels.

## Auditoria de rascunhos
- Amostra: 100 rascunhos retornados pelo WordPress, até 100 mídias do recorte da biblioteca; não afirmar cobertura de todos os rascunhos/mídias da conta.
- 87 com imagem destacada, 13 sem imagem; 59 com crédito ou alt ausente; 85 exigem revisão documental/visual ou não puderam ser esclarecidos no recorte. Contagens são triagem conservadora, não diagnóstico de marca d'água em 85 imagens.
- Exemplos críticos: #9708→mídia #9707, #9702→#9701, #9693→#9692; arquivos `featured-N.jpg/webp` sem comprovação de licença ou alt no inventário. **Não apagar em lote**. Gate rc10.4 os classifica como bloqueados até revisão.
- A mídia #9704 foi preservada na biblioteca para evitar quebra de outras referências; antes de excluir, auditar usos cruzados e direitos.

## Causa técnica e limites do processo
- `pipeline_rss.py`: chama `plan_image(..., offline=False)` para **planejar/pesquisar**, mas não faz upload nem associa automaticamente a candidata licenciada.
- A capa é fornecida ao fluxo de rascunhos pelo argumento independente `featured_media_id`, com confirmação manual booleana `media_rights_confirmed`; `wp_draft_staging.py` verifica tipo MIME e alt, mas não o efetivo laudo de direitos e branding.
- Portanto, a pesquisa de banco gratuito pode produzir uma candidata e ainda deixar uma imagem previamente fornecida/legada associada; não há garantia de substituição automática. Não temos log original de outubro do #9705 para atribuir com certeza a origem da mídia #9704, nem comprovação de execução de **todos** os módulos editoriais.
- O Gate anterior avaliava imagem válida + legenda mínima, sem origem/licença documentada, logo podia aceitar uma foto com watermark.
- A rc10.4 aprimora **triagem documental**, não reconhecimento visual automatizado; legendas e descrições são declarações e necessitam verificação de direitos e imagem final.
- O texto do #9705 ainda precisa de revisão substantiva e autoria/transformação, pois reproduz a estrutura e vivências do artigo original de Ben Schoon no 9to5Google (25/10/2026).

## Homologação restante (NÃO CONCLUÍDA)
1. Executar suite Python atualizada de `tests/test_image_protocol.py` e regressões no checkout do executor MKT-RSS; testes PHP locais não substituem esses.
2. Identificar Python 3.10+ no host e ligar o código atualizado ao processo **real** que cria drafts. `~/mkt-rss-shopee-check` existe no SSH Hostinger, mas o Python padrão mostrado é 3.6.8 e não há comprovação de worker automático. Nenhum cron novo, GitHub Actions ou serviço contratado.
3. Executar rascunho de ponta a ponta com credencial MKT-RSS, manifesto licenciado, foto validada em 390/1440 e retorno ao Gate; confirmar que erros bloqueiam associação e aprovação. Fazer checagem visual de todas as capas suspeitas, não inferir licença a partir do nome do arquivo.
4. Somente após evidência de execução verificável, declarar automação de geração e troca de imagem concluída.

## Estado de segurança
Sem aprovação de proprietário, sem publicação, sem deletar imagens antigas. rc10.4 trata pendências de mídia em `cxgna_draft_readiness()`, impedindo aprovação por falta de prontidão técnica.
