# M05.5-I — Inventário Vercel e piloto único supervisionado
Data: 2026-10-26. PR #20. Somente inspeção e preparação, nenhuma chamada externa à IA.

## Resultado Vercel (conector, leitura)
- Quatro projetos existentes: conexo-jules-mcp-staging, conexo-jules-mcp-preview, conexotech-panel, my-git.
- Vercel Edge Configs retornou [].
- Instalações de integrações Vercel retornaram [].
- Listas de variáveis de ambiente de cada um dos quatro projetos retornaram envs=[], com hiddenProductionEnvCount=0.
- Isso NÃO prova ausência de toda infraestrutura externa ou variável fora desse escopo, mas nenhum armazenamento transacional compartilhado ou Groq configurado foi identificado nessas consultas.
- Não foram expostos valores secretos, e nenhum recurso foi provisionado.

## Situação CI
- O workflow editorial mais recente estava verde. CI geral do commit 029ce69 falhou por cinco testes do ledger que assumiam filesystem local, mas rodavam com GITHUB_ACTIONS=true.
- A correção em testes/test_m055d_cloud_budget_preflight.py desativa GITHUB_ACTIONS somente nas simulações locais da fixture e preserva o teste dedicado que reativa a variável para verificar bloqueio no runner.
- O resultado da CI pós-correção precisa ser confirmado; não declarar PASS sem run concluído.

## Piloto de uma única execução — somente especificação, não autorizado
1. Fonte real e snapshot com data; aprovação de um provedor Groq/limite de orçamento explícitos.
2. Orçamento por uma única execução, identidade da tentativa e isolamento de concorrência; nenhuma chamada recorrente, nenhuma tarefa agendada.
3. A restrição de segurança atual bloqueia o Groq no GitHub Actions com SQLite efêmero; não contornar o gate alterando GITHUB_ACTIONS em produção.
4. Somente após uma solução segura para persistência ou aprovação de mecanismo alternativo verificável, executar 1 ensaio supervisionado com max_tokens limitado e evidências completas.
5. Auditar título, metadados, corpo, preço/data, JSON-LD e HTML; realizar contraprovas negativas, revisão independente e manter escreveu=False.
6. Nenhuma criação de rascunho WordPress faz parte da execução; deve ser autorizada separadamente.

## Decisão
Não contratar nem instalar novo banco. A infraestrutura existente verificada não demonstrou armazenamento compartilhado confiável. Manter piloto real e escrita WP BLOQUEADOS; desenvolver documentação/testes no GitHub sem custos de IA.
