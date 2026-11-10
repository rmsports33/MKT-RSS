# Memória do Projeto — MKT-RSS / MDA AUTO

## Desenvolvimento substantivo — precedência 10/11/2026

- Online, importar artigo pendente inclui planejamento, adaptação e crítica pelo
  provedor existente automaticamente. `--adapt-editorial` força nova adaptação;
  não é requisito de execução dos módulos. `--offline` preserva o insumo e registra
  as pendências; não inventa redação, voz aplicada ou aprovação.
- RSS prepara briefing quando necessário e critica o texto final, incluindo
  atribuição e links, com até duas redações. Falha de provedor permanece pendente.
- Briefing define leitor, necessidade, recorte, contribuição e limites. Avaliação
  substantiva exige justificativa e trechos literais vinculados ao texto e briefing;
  PROMPT_APPLIED isolado não aprova qualidade. Crítica pode usar o mesmo modelo:
  declarar revisão assistida, nunca independência ou aceite humano inexistentes.
- Adaptação feita por Codex/ChatGPT pode usar ASSISTED_ADAPTED com hash do conteúdo;
  nunca usar HUMAN_ADAPTED para personificar o proprietário nem alegar chamada de
  system prompt externo que não ocorreu. Edição invalida a avaliação textual.
- Aplicar até três links internos realmente relacionados; não completar quota com
  links irrelevantes. Links internos presentes sem verificação continuam pendentes.
- No workflow manual, github.sha fixa o código da própria execução e evita rodar
  um snapshot antigo depois de corrigir o motor. Não ativa cron nem publicação.
- Critério técnico não certifica fatos nem padrão acima da média. Artigo final e
  recibo da versão continuam necessários para revisão do proprietário.

## Gate editorial obrigatorio — 10/11/2026

- Toda rota de geração/importação passa pelo mesmo módulo de prontidão. Aplicar a identidade não pode ser inferido do nome da marca nos metadados.
- O gerador MKT-RSS registra hashes do DNA e do prompt. Importações aceitam prova verificável de outro provedor ou atestado humano vinculado ao hash do Markdown; sem prova, recebem `persona_editorial_nao_aplicada` e não podem ser declaradas completas para revisão.
- Toda execução produz lista de módulos, manifesto por versão e status de conclusão. `EXECUTED` não significa `PASS`; mudanças no conteúdo invalidam o recibo anterior.
- Apresentar ao proprietário o artigo completo e o manifesto correspondente; nunca perguntar se os módulos devem ser usados. A revisão humana do conteúdo e a autorização de publicação continuam separadas.
- Detalhes: `docs/EDITORIAL_ORCHESTRATION_GATE_20261110.md`.

## Precedencia do usuario — 08/11/2026

MKT-RSS e o motor completo e unico publicador do fluxo RSS. ChatGPT e apoio opcional: nao exigir conversa, sessao Work ou servico Conexo OS em execucao para operar. O validador Conexo OS fixado por hash continua dependencia de codigo, nao outro publicador. Uma identidade WordPress de editor de servico MKT-RSS basta; revisao e aprovacao humanas continuam independentes e vinculadas a versao. Contrato preparado: `docs/MKT_PRIMARY_PUBLISHER_20261108.md`. Instalacao/configuracao real e aprovacao de artigo sao etapas distintas da integracao de codigo.

`--handoff-only --handoff-dir` bloqueia escrita remota mesmo com flags de rascunho ativas. Pacotes mantem revisao humana pendente; `--research-context` nao aprova conteudo. Preservar pesquisa gratuita de imagens, proveniencia e validacao de direitos; imagem extraida do RSS nao autoriza reutilizacao.

## Decisões vigentes e precedência — 05–06/11/2026

- **MKT-RSS é motor editorial completo**, não mero alimentador RSS: preservar coleta, filtros, pesquisa/insumos de fontes complementares, redação Groq Free ou outro provedor autorizado, DNA ConexoTech, SEO, mídias com direitos verificados, pacote com hash, links relacionados e criação de rascunhos privados. ChatGPT-first é o colaborador de apuração/revisão, não o substituto obrigatório do MKT-RSS. O WordPress REST/MCP também pode operar diretamente uma pauta sem exigir que Python esteja ativo.
- **Um só fluxo de evidências e publicação**, com executores intercambiáveis (ChatGPT/Work, Python MKT-RSS, OpenCode). Um escritor por artigo/versão, idempotência e readback. Proibição de publicar automaticamente sem aprovação factual/substantiva e aceite explícito; `PENDING_HUMAN_REVIEW` jamais é autorização.
- **Funcionamento antes de burocracia desnecessária:** rascunhos privados e edição supervisionada não dependem de staging, SFTP, HMAC, migração Native SEO nem novo hosting. Respeitar Gate realmente ativo. Segurança mínima (credenciais, duplicidade, direitos de mídia, revisão humana para publicação) permanece inegociável. Rank Math vigente até homologação de substituição.
- **Produtividade:** reutilizar ferramentas testadas, desenvolver só pendências, demonstrar uma funcionalidade antes de ampliar; cloud-first, sem PowerShell obrigatório, sem cartão/custos extras. Não abrir novos executores ou auditorias extensas sem necessidade concreta.
- **Situação comprovada em 06/11:** RSS real → Groq Free → pacote → draft WordPress #9769 com readback, mas artigo ainda superficial, sem imagem/links internos e com uma fonte. A branch `feat/editorial-dna-multisource-20261105` contém avaliação de prontidão, pesquisa multifonte via contexto identificado e seleção opcional de links publicados do WP. **Esta branch não foi mesclada à master**; workflow manual pinado a SHA auditado e coleta diária `daily.yml` opera somente `--queue-only`, sem Groq nem WP.
- A nota editorial é proporcional ao gênero, não uma contagem fixa universal. Rascunhos podem seguir como candidatos pendentes; somente artigos com fatos verificados, direitos de mídia, revisão e autorização da versão entram na publicação. Expor somente manifesto seguro no Actions público; nunca artigo não revisado, credenciais ou claims.
- Fonte central: `rmsports33/conexo-os:main/AGENTS.md` (padrão unificado) e `docs/EDITORIAL_DNA_V1.md`. Corrigir regras antigas divergentes em vez de criar duas arquiteturas.

## Regra durável de execução editorial — 03/11/2026

**ChatGPT-first com WordPress REST/MCP é uma via supervisionada preferencial, não um executor exclusivo.** O MKT-RSS permanece o motor completo da automação RSS. O WordPress autenticado cria/edita rascunhos e publica/agenda artigos supervisionados. NÃO pedir executor Python permanente, Windows/PowerShell, OpenCode, GitHub Actions, Vercel, novo hosting ou Hostinger MCP como pré-requisito. O Python deste repositório é componente opcional de RSS/transformação/teste; a flag `CONEXO_RSS_DRAFT_STAGING=1` preparada no PR #39 não define a arquitetura operacional.

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

## Precedencia expressa do proprietario - 08/11/2026

O usuario autorizou "Autorizar aprovacao pelo proprietario" para resolver a publicacao do artigo #9768 sem trocar sua autoria nem criar terceiro usuario. RC5 permite o aceite humano explicito do proprietario verificado ID3, vinculado ao snapshot, SEO e evidencias de qualidade. O publicador tecnico MKT-RSS ID4 permanece impedido de aprovar e continua sendo o unico publicador desse fluxo.

Esse modo se registra como review_mode=owner e nao representa revisao independente por outra pessoa. Nao fabricar conferencia visual, fatos, aceite ou assinatura. A tela administrativa exige verificacao humana; texto alterado invalida a aprovacao. HMAC privada, Turso, leitura de confirmacao, reserva por versao e SEO assinado continuam obrigatorios no publicador MKT-RSS do modo owner. A politica anterior de impedir autor=aprovador continua para o modo independent; a excecao autorizada e restrita ao proprietario e exige papel administrativo vigente.

MKT-RSS e o motor prioritario e o publicador; ChatGPT e apoio opcional. Fluxo e evidencias: docs/OWNER_APPROVAL_20261108.md. Nunca transformar um teste verde em aprovacao editorial ou desativar o Gate para publicar.
