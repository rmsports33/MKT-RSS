# Memória do Projeto — MKT-RSS / MDA AUTO

## Integração de identidade editorial — 05/11/2026

**O MKT-RSS é motor editorial completo**, não apenas coletor de pautas/rascunhos. Preservar coleta, filtragem, enriquecimento com fontes, redação, imagens, SEO, validação e entrega ao WordPress. ChatGPT é colaborador editorial complementar (pesquisa, análise, revisão e aperfeiçoamento), nunca substituto obrigatório do MKT-RSS.

Usar `mkt_flow_p0/editorial_identity.py` como contrato executável de voz, ligado ao DNA oficial `conexo-os/docs/EDITORIAL_DNA_V1.md`. Ao acrescentar fatos, informar sua URL e manter revisão humana pendente; jamais inventar fontes, testes ou declarar `approved`. O handoff JSON da redação conserva identidade, origem RSS, fontes, Markdown, SEO e hash de versão para o fluxo ChatGPT-first. `pipeline_rss.py --research-context` associa a pesquisa a uma única pauta por URL; nenhuma publicação é autorizada por esse arquivo. Instruções: `docs/DNA_EDITORIAL_MULTIFONTE_CHATGPT_20261105.md`.

## Protocolo de recuperação operacional — 05/11/2026 (prioridade sobre escolhas de ferramenta)

**FUNCIONAR PRIMEIRO, SEM REFAZER A INFRAESTRUTURA.** A entrega prioritária é 1 artigo de qualidade no ciclo prévia → rascunho → revisão/aceite → publicação manual/supervisionada → leitura de confirmação. Não bloquear rascunho por staging, SEO nativo, readiness HMAC, migração cloud, runner, novo conector, auditoria ou cron. O staging é opção de teste de infraestrutura, não requisito para o rascunho no WordPress existente. Reusar resultado comprovado e testar só a diferença atual.

**Dois caminhos, nunca misturar:** (A) via rápida: WordPress nativo com operador autenticado, rascunho privado e publicação humana de versão aprovada, mantendo Rank Math. (B) automação estrita: gate assinado, idempotência e readback; desenvolver separadamente, sem bloquear (A). Nenhum agente deve usar a via rápida para contornar um Gate efetivamente ativo no destino.

**Controles mínimos inegociáveis:** credenciais não expostas, permissão WordPress real, revisão factual/substantiva e aceite específico antes de publicar, não duplicar posts sem verificar slug, confirmar conteúdo/status depois de escrever, preservar recuperação. Não remover o site do ar ou escrever em produção por inferência: a autorização da operação concreta continua obrigatória. Sem custos extras nem execução automática oculta.

**Regra de produtividade:** iniciar pela última operação bem-sucedida; sem reabrir bloqueios resolvidos. Se uma ferramenta falhar, escolher a próxima já conectada. Um objetivo por sessão; novas verificações só quando o código, o destino ou o risco mudarem. Registrar apenas entrega, prova, bloqueio concreto e próximo passo. Manual: `docs/PROTOCOLO_RECUPERACAO_OPERACIONAL_20261105.md`.

## Regra durável de execução editorial — 03/11/2026

**Executor é escolha operacional, não requisito de produto.** Usar primeiro o WordPress REST/MCP já autenticado; se OpenCode ou o cliente Python existente estiver funcionando melhor, reutilizá-lo sob as mesmas permissões e revisão editorial. Não exigir Windows/PowerShell, staging, HMAC, GitHub Actions, FTP/SFTP, Vercel, novo hosting ou Hostinger MCP para gerar prévia e criar um **rascunho privado**. A publicação supervisionada usa as permissões nativas do WordPress quando o Gate não está ativo; quando o Gate estiver ativo, respeitar as restrições reais do destino. A flag simples `CONEXO_RSS_DRAFT=1` ativa apenas envio de rascunho (a antiga `CONEXO_RSS_DRAFT_STAGING=1` continua aceita por compatibilidade). Nunca eleva um rascunho a `publish` automaticamente.

**Operação supervisionada ≠ automação estrita:** rascunho não precisa certificação de publicação; publicação exige revisão factual e substantiva, fontes, imagem autorizada, aceite específico da versão e confirmação no WordPress. Gate assinado e SEO nativo v0.5.2 permanecem iniciativa de automação futura, sem bloquear artigos supervisionados enquanto Gate está inativo e Rank Math segue ativo. Não desativar as proteções próprias do transporte assinado para publicar sem revisão.

A divisão Work (operação) / Codex Cloud (engenharia) é temporária para desbloquear a geração e publicação; não é arquitetura permanente de dois sistemas. Não confundir autorização genérica para corrigir com aprovação de artigo. Fonte central: Conexo OS `AGENTS.md` em `main` e plano de unificação PR #46. Registrar mudanças e evidências sem inferir deploy por CI.

## Diretrizes operacionais

- Consultar o [Contrato Operacional](https://github.com/rmsports33/conexo-os/blob/ec190d6b6c62df3235905499ee84eeb75ad9507d/docs/CONTRATO_OPERACIONAL.md), a política de execução e o protocolo de tarefas do núcleo.
- Priorizar entregas do ConexoTech, reaproveitar componentes e evidências e registrar escopo, branch/SHA, critérios, testes, bloqueios e próxima ação na issue/PR.
- Pesquisa de ferramentas é condicional a uma lacuna real. Antes de nova dependência, comparar capacidades existentes e consumidores; não repetir pesquisa em toda tarefa.
- Aplicar o [DNA reconciliado](https://github.com/rmsports33/conexo-os/blob/ec190d6b6c62df3235905499ee84eeb75ad9507d/docs/EDITORIAL_DNA_V1.md): voz inteligente e acessível, estrutura por gênero, fontes rastreáveis e contribuição verificável.
- Reinaldo Mendes é o autor humano; Conexo Insight é voz interna. Não inventar testes, números, preços ou experiências próprias.
- SEM_ALERTAS não comprova factualidade. Preservar o bloqueio de escrita quando o gate factual não estiver integrado.
- Trabalhar em branch isolada, validar proporcionalmente e preservar mudanças preexistentes. Merge, deploy, publicação e custos dependem do escopo autorizado.
- Drive V3 continua oficial; memória não concede autorização. Não ativar publicação ou agendamentos ao aplicar estas diretrizes.
