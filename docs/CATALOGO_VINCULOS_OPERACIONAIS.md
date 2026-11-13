# Vínculos operacionais de produtos — RSS → fila → WordPress

Implementação no próprio MKT-RSS, sem outro banco, executor ou agendamento.

## Contratos

- **Fonte canônica:** `mkt-flow-escrita/pautas/catalogo-produtos.json`, somente cadastro/referência. A tabela `rss_product_links` usa o **mesmo banco** da fila `rss_pautas` (Turso quando configurado; SQLite isolado quando explicitamente selecionado).
- **Na coleta RSS normal:** apenas uma classificação `CANDIDATE_MATCH` do catálogo permite tentar gravar um vínculo. A pauta precisa ter sido registrada ou encontrada e sua URL canônica precisa corresponder exatamente à notícia atual. Repetir a mesma notícia é idempotente; notícias diferentes sobre o mesmo produto têm `pauta_id` distintos.
- **Durante `--dry-run`:** não é criada tabela nem vínculo, e nenhuma consulta ao Turso é feita.
- **No WordPress:** `pipeline_rss.py` só tenta vincular um rascunho após `stage_rss_draft` retornar `acao=publicado_rascunho`, `status=draft` e `post_id` inteiro positivo, isto é, após readback do WordPress. Não cria pauta substituta, não transforma rascunho em publicado, não muda estado editorial, não chama WP além da operação existente.
- **Falhas:** uma falha no vínculo posterior a um registro de pauta ou rascunho já ocorrido não desfaz nem repete a operação principal. O recibo sinaliza `LINK_PERSISTENCE_PENDING` ou contadores de vínculo pendente. Sem fila pré-existente, o recibo indica `SKIPPED_NO_QUEUE_LINK`; evitar inventar IDs de pautas.
- **Qualidade / publicação:** `publication_authorized=false` em todos os recibos auxiliares. O Gate Único e os contratos de aprovação por versão permanecem independentes.

## Limites da ativação

A implementação foi preparada para a coleta e para o estágio de rascunhos do executor já existente. Nenhum backfill automático de pautas ou artigos foi executado. O catálogo não sincroniza arquivos JSON a cada evento; a tabela operacional guarda os vínculos. Antes da homologação real, testar criação/idempotência/conflito/indisponibilidade com SQLite isolado, executar regressões do MKT-RSS e uma homologação autenticada em ambiente autorizado e sem publicação.

O campo `wp_status` da tabela atualmente representa apenas o estado `draft` confirmado no readback; atualização futura para `publish` ou `future` exige fonte autenticada, Gate e validação separados. Nunca inferir publicação da simples existência de um post ID.

## Ativação controlada

A gravação de vínculos é **desativada por padrão**. Requer `CONEXO_PRODUCT_LINKS_ENABLED=1` no executor existente; não habilitar a variável antes de testes de regressão, homologação em base isolada e confirmação da identidade do banco. No modo desativado, a classificação RSS permanece disponível e nenhuma tabela de vínculo é criada por esses caminhos. O opt-in não autoriza publicação, não habilita WP por si e não executa backfill.

## Uso pelos fluxos já existentes

- `.github/workflows/daily.yml` ativa `CONEXO_PRODUCT_LINKS_ENABLED=1` durante a coleta diária **somente** com `CONEXO_PRODUCT_LINKS_ENABLED=1`; o fluxo legado da fila é preservado e **apenas os vínculos novos** falham de maneira controlada quando não há Turso, sem fallback SQLite silencioso.
- `.github/workflows/rss-homolog-manual.yml` fornece as credenciais Turso existentes apenas no passo de criação/reutilização de rascunho privado. Não permite publicar nem aciona chamadas de IA além das já previstas no modo manual.
- `product_links.py` **não usa SQLite por engano** quando executado sem `db_path` explícito e sem credenciais Turso; nesse caso informa vínculo pendente. SQLite continua possível apenas em testes isolados que passam `db_path`.
- O código e os testes podem ser integrados antes da primeira coleta operacional; esta integração **não comprova** uma escrita/readback real de vínculo no Turso nem um novo rascunho WordPress. Essas provas exigem execução autenticada da respectiva rotina e conferência posterior.
