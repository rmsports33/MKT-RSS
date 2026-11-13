# CHECKPOINT DE RETOMADA — 14/11/2026 — ConexoTech / Conexo OS / MKT-RSS

Registro das pendências da sessão encerrada em 13/11/2026 (aprox. 18h55 BRT).
**Este checkpoint documenta o estado; não declara implantação nem testes não executados.**

## Estado confirmado
- WordPress de produção: `https://conexotech.com.br`.
- Gate Editorial Único `0.1.0-rc10.4` instalado e ativo, verificado na lista de plugins; publicador legado `conexo-gate-agenda-nativa` inativo.
- Conta editorial ID 4, credencial de aplicação `Conexo MKT-RSS` vinculada ao Gate, conforme screenshot do painel, **sem homologação pelo processo MKT-RSS**; aprovação humana permanece com proprietário ID 3. Não registrar senhas/UUIDs neste arquivo.
- Artigo #9705 "What tech is making you happy? – Gadgets que trazem alegria": `draft`, mídia destacada **#9888**, Fitbit Inspire 3, Tatsuo Yamashita/Wikimedia Commons, licença CC BY 4.0, fonte, alt e legenda registrados. Capa antiga #9704 (featured-60.jpg) tinha branding 9to5Google, foi desvinculada e preservada na biblioteca. Gate exibiu #9705 em `Revisão humana` sem pendência técnica, mas **isso não é aprovação editorial ou prova de checagem factual/voz**.
- Artigo #9687 publicado por aprovação humana em teste anterior; não confundir com homologação de agendamento/automação.
- `mkt_flow_p0/image_protocol.py`: validação fail-closed de manifesto de imagem, exigindo `third_party_branding_review=PASS_NO_THIRD_PARTY_BRANDING` e `visible_third_party_branding is False`; testes de regressão adicionados em `tests/test_image_protocol.py`. Commits `e3048736`, `c3bbcb3`. **Testes Python ainda não executados no executor real**, detecção por pixels não implementada.
- MKT-RSS tem `conexo_remediation.py` e hook `_post_persist_remediation` opt-in (`CONEXO_GATE_REMEDIATION_AUTO=1`) em `wp_draft_staging.py`; primeira correção do #9705 foi feita pela conexão administrativa WordPress, **não pelo executor usando senha de aplicativo**.
- No SSH Hostinger, `~/mkt-rss-shopee-check` existe; `python3 --version` retornou `3.6.8`, `python3.11` e `python3.12` não estavam no PATH. O usuário também já operou `~/mkt-rss-runner` com `.venv/bin/python` e `ops/hostinger/run_rss_queue.sh --preflight` PASS; Turso `TURSO_READ_OK`; **esse outro checkout/venv deve ser priorizado na próxima inspeção, antes de qualquer instalação**. O preflight é somente de leitura e não prova agendamento ativo; houve `BLOCKED: schedule not activated`.
- Backups Turso `mkt-rss.sql` e `mkt-rss-homolog.sql` validados por `sha256sum -c SHA256SUMS` (ambos OK).

## Pendências ordenadas (sem criar outro agendador, custos ou Actions)
1. **Localizar executor editorial correto na Hostinger**: diferenciar `~/mkt-rss-runner` (com `.venv` e preflight PASS) de `~/mkt-rss-shopee-check` (Python 3.6.8). Verificar `~/mkt-rss-runner/.venv/bin/python --version`, git remotes/status, serviços/jobs existentes e a execução real de `run_rss_queue.sh`. Não assumir que o checkout da Shopee é o executor principal. Sem `git pull` sobre alterações locais; sem credenciais em logs/chat.
2. **Homologar testes Python** `tests/test_image_protocol.py` e regressões de pipeline RSS, stock media, staging de rascunhos e correção; registrar PASS/FAIL reproduzíveis, não confundir lint com testes. Identificar e corrigir incompatibilidades de versão antes de implantar.
3. **Instalar código atualizado no executor existente** com revisão do diff, backup e rollback; confirmar que a versão executada é a de commits validados. **Não criar cron, serviço, GitHub Actions ou deployment paralelo**.
4. **Testar a credencial exclusiva MKT-RSS**: autenticar no WordPress usando segredo armazenado no próprio executor, somente rotas permitidas; uma única correção de excerpt de um draft apropriado (ex.: #9708 *apenas após leitura fresca* e checagem de fatos), com readback WordPress + Gate. Garantir que não aprova/publica e que 401/403 bloqueia fail-closed. Não expor senha ou UUID. Revisar risco residual de permissões da conta editorial ID 4 e outros canais de escrita.
5. **Automatizar preparação de imagem no caminho efetivo**: `pipeline_rss.py` pesquisa `plan_image(...,offline=False)` mas **não baixa, registra nem associa** automaticamente candidata licenciada; `featured_media_id` externo e `media_rights_confirmed` booleano podem contornar o fluxo documental. Exigir manifesto de proveniência, licença, revisão visual dos recortes finais 390/1440, consistência de mídia, sem watermark/logo de portal, e auditoria de versão, antes de anexar. Não remover marcas por recorte/edição para tentar contornar direitos.
6. **Integrar bloqueios realmente à API de escrita/publicação do Gate em produção** (não só ao painel): checar tentativas de publish por REST, agendamento, XML-RPC se habilitado, credenciais de app, endpoints próprios, revisões/versionamento e WP-Cron. Não declarar cobertura de todos os caminhos sem ensaios live e rollback.
7. **Auditoria de imagens em outros rascunhos**: amostra de 100 drafts; 87 com capa; 13 sem capa; 59 com crédito ou alt ausente; dezenas de `featured-N.jpg/webp` suspeitos documentalmente. Não inferir logo pelos nomes; verificar pixels, licença e uso cruzado, priorizar #9708→#9707, #9702→#9701, #9693→#9692. Não excluir mídias em lote nem inventar licenças.
8. **Artigo #9705: revisão editorial substantiva obrigatória** antes de qualquer aprovação; verificar fatos e plausibilidade de produtos ("Googlebook", "Fitbit Air", "iPhone Duo" etc.), origem/atribuição, atualidade, independência da redação em relação ao texto 9to5Google, persona editorial ConexoTech, links internos, fontes independentes e conteúdo completo. Refazer texto se necessário; a nota do Gate e a ausência de pendências técnicas NÃO asseguram que todos os módulos foram executados.
9. **Auditar mecanismo integral de geração**: registrar trilha verdadeira por etapa (ingestão RSS, pesquisa, fontes, factualidade, reescrita, voz, SEO, imagem, mídia, conferência visual, versão, Gate); identificar quais módulos foram executados/ignorados no #9705. Sem log original da geração de outubro não afirmar causa histórica específica; causa arquitetural já identificada: pesquisa de imagem desacoplada da associação final.
10. **Simplificar revisão humana** sem perder garantias: substituir 13 caixas por relatório de evidências + uma aprovação humana por versão, apenas quando verificações automáticas estiverem de fato implantadas e critérios editoriais essenciais tiverem prova suficiente.
11. **Agendamento e operação contínua**: só depois de execução única comprovada, usar mecanismo de execução JÁ EXISTENTE (preflight anterior indicou schedule não ativado), evitar novo cron/serviço. Confirmar alarmes, erros 429, reentrância, idempotência, estado Turso e logs, mantendo publicação controlada.

## Ordem recomendada para a primeira sessão do dia 14/11
A. Inspecionar diretamente o checkout `~/mkt-rss-runner` e o `.venv` já comprovados, não iniciar pelo checkout Shopee.
B. Rodar testes regressivos em ambiente compatível, sem efeitos WordPress.
C. Homologar uma operação autenticada somente de correção, com readback.
D. Revisar mecanismo de seleção/associação de imagem e qualidade factual do #9705.
E. Reavaliar fila e evidências; nenhuma publicação sem aceite humano.

## Restrições permanentes
Cloud-first, preferência por Hostinger/Turso/WordPress/GitHub existentes, sem gastos, sem Actions, sem staging, sem duplicar serviços, sem segredos nos chats, sem publicação automática não aprovada. Revisão humana uma vez, sobre artigo completo e versionado.

## Evidências em repositório
- `docs/IMAGE_GATE_AUDIT_2026-11-13_POST9705.md` (commit `facb9e09`).
- `docs/GATE_REMEDIATION_EXISTING_HOSTINGER_EXECUTOR.md` (commit `d21e8d46`), cuja referência exclusiva a `mkt-rss-shopee-check` deve ser corrigida à luz do checkout `~/mkt-rss-runner` comprovado.
