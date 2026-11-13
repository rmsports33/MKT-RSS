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

## Primeira prova operacional real (13/11/2026)

- Resultado: **PASS** na execução GitHub Actions https://github.com/rmsports33/MKT-RSS/actions/runs/43429868861
- Gatilho pontual autorizado: issue https://github.com/rmsports33/MKT-RSS/issues/117
- Fonte RSS real: GSMArena, notícia https://www.gsmarena.com/motorola_signature_27_battery_capacity_germany-news-75468.php
- Produto canônico: `motorola-signature-27`
- Pauta gravada no Turso existente: `db04160bd336123bbb3046654060a27d`, estado `DESCOBERTA`, `queue_new=true`
- Vínculo `product_id + pauta_id`: 1 registro com chave única, confirmado por duas consultas SQL SELECT de leitura posterior autenticada
- Resultado: `authenticated_turso_readback=true`, `publication_authorized=false`, `wordpress_modified=false`, `wp_post_id=null`
- A prova utilizou `registrar()` e `link_pauta()` existentes, sem IA/Groq, WordPress, publicação, agendamento ou novo executor.
- Foram removidos workflow/script/teste temporários da prova após a coleta dos registros; o mecanismo operacional de vínculos permanece ativo no fluxo RSS.
- **Escopo:** comprova `RSS real → pauta Turso → vínculo Turso → readback`. Não comprova `readback WordPress → vínculo com wp_post_id`, que depende de um rascunho válido produzido no fluxo editorial normal.

## Consolidação de persistência sem Actions (13/11/2026)

- `link_pauta` exige `SELECT` posterior à tentativa de inserção; não devolve `LINKED` quando a linha não existe ou a URL é diferente.
- `link_verified_draft` preserva todas as pré-condições de readback WP do adaptador e, após o `UPDATE`, invoca `verify_draft_link` no **mesmo banco da fila**. Somente evidência SQL de `wp_post_id` exato e `wp_status=draft` em todas as linhas correspondentes devolve `DRAFT_LINKED`.
- Se o SQL devolve ACK mas não persiste, retorna `LINK_READBACK_PENDING`, nunca sucesso falso. Exceções de acesso ao Turso são tratadas pelo chamador como pendência auditável, sem repetir o POST do WordPress. `verify_draft_link` é consulta SQL de vínculo e **não** substitui a leitura autenticada do próprio WP.
- `list_links` exige explicitamente Turso quando não recebe `db_path`, impedindo interpretação enganosa de SQLite local vazio como o banco de produção.
- O teste isolado offline executado fora do GitHub cobriu sete cenários: dois eventos distintos/duplicação, URL incompatível, criação/reuso, publicação proibida, falta de credenciais, falsa confirmação de persistência e falha no banco. Três regressões equivalentes foram registradas em `tests/test_product_links_operational.py`. **A suíte completa não foi reexecutada após esta mudança**, para preservar a franquia.
- Não houve escrita no WordPress nem no Turso real nesta consolidação. A comprovação operacional final requer rascunho legítimo com URL de origem idêntica à da pauta já existente e credenciais autenticadas no executor já autorizado, com readback WP + Turso. Não acionar CI/GitHub Actions para fabricar prova.
