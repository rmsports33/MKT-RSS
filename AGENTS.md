# Memória do Projeto — MKT-RSS / MDA AUTO

## Regra durável de execução editorial — 03/11/2026

**ChatGPT Work / ChatGPT-first com WordPress REST/MCP é o executor editorial escolhido.** O WordPress autenticado cria/edita rascunhos e publica/agenda artigos supervisionados. NÃO pedir executor Python permanente, Windows/PowerShell, OpenCode, GitHub Actions, Vercel, novo hosting ou Hostinger MCP como pré-requisito. O Python deste repositório é componente opcional de RSS/transformação/teste; a flag `CONEXO_RSS_DRAFT_STAGING=1` preparada no PR #39 não define a arquitetura operacional.

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
