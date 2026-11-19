# Política de consolidação contínua e sanitização — MKT-RSS

**Decisão operacional: 18/11/2026.** Esta política aplica-se ao código, testes, documentação, branches e PRs do MKT-RSS e complementa o `AGENTS.md`, o contrato editorial e os controles de publicação. Ela é compatível com a política transversal do Conexo OS; prevalecem sempre as decisões mais recentes do proprietário e as salvaguardas mais restritivas.

## Objetivo

Impedir que melhorias prontas, correções locais, branches e PRs permaneçam indefinidamente isolados. O desenvolvimento deve produzir uma base progressivamente integrada, verificável e mais simples, sem sacrificar segurança, rastreabilidade, continuidade ou autonomia entre ferramentas.

## Regras obrigatórias

1. **Trabalho pronto deve chegar a um commit.** Toda alteração concluída e validada deve ser registrada em commit coerente. Não deixar mudanças prontas apenas no diretório de trabalho, em arquivos temporários ou em instruções de conversa.
2. **Preservar alterações locais.** Antes de editar, trocar de branch, rebasear ou limpar, identificar mudanças modificadas, não rastreadas e ignoradas relevantes. Preservar, classificar e atribuir destino. Nunca sobrescrever trabalho do usuário ou de outro agente.
3. **Toda branch/PR precisa de objetivo e próximo passo.** Registrar escopo, base, head/SHA, arquivos, dependências, validações, bloqueios e próxima ação. PR sem atividade deve ser concluído, encerrado com justificativa ou mantido explicitamente bloqueado — nunca esquecido.
4. **Integrar assim que estiver pronto e seguro.** Depois da revisão proporcional ao risco e das validações necessárias, encaminhar para integração na branch de desenvolvimento apropriada. Não acumular melhorias independentes para formar lotes artificiais. Isso não autoriza merge automático.
5. **Separar commit, merge e deploy.** São marcos distintos. Esta política não autoriza merge, deploy, publicação, escrita em WordPress/Turso, alteração de Gate/cron, DNS, credenciais ou produção.
6. **Classificar cada pendência.** Usar PRONTO_PARA_COMMIT, COMMITADO, EM_REVISAO, PRONTO_PARA_INTEGRAR, INTEGRADO, BLOQUEADO ou OBSOLETO. Cada item deve ter uma referência rastreável, destino e próxima ação.
7. **Resolver dependências na ordem correta.** Agrupar apenas mudanças tecnicamente coerentes. Um bloqueio não deve paralisar trabalho independente nem justificar contornos de controles humanos ou técnicos.
8. **Testar proporcionalmente ao risco.** Começar pela fronteira afetada e ampliar para a suíte pertinente quando necessário. Não repetir testes ou auditorias sem mudança de código, ambiente, evidência ou hipótese técnica.
9. **Distinguir regressões de falhas preexistentes.** Comparar com a base relevante quando necessário. Registrar falhas, skips e limites; nunca declarar PASS para testes não executados.
10. **Sanitizar progressivamente.** Remover duplicações, código morto, caminhos obsoletos e inconsistências diretamente no escopo e com baixo risco. Refatorações amplas exigem critérios e proteção contra regressões.
11. **Manter documentação coerente.** Atualizar contratos, instruções e inventários afetados. Registrar evidência real, limites e data da leitura. Documentação não substitui teste nem prova de operação.
12. **Fechar cada ciclo.** Registrar commit verificável, validações, destino de integração, pendências, bloqueios e próxima ação. Se merge não estiver autorizado ou seguro, deixar a revisão preparada e indicar o impedimento concreto.
13. **Garantir continuidade entre ferramentas e agentes.** A fonte de verdade é o repositório e seus artefatos versionados. Não depender de memória de IA, agente específico ou computador pessoal.
14. **Evitar cerimônia sem valor.** Reutilizar mecanismos existentes. Não criar Actions, workflows, issues, PRs, relatórios, serviços ou agendamentos redundantes. Respeitar a política de economia de Actions e custos do projeto.
15. **Preservar os controles editoriais.** Gate, autoria, direitos de mídia, proveniência, revisão e aprovação humana vinculada à versão permanecem obrigatórios. Testes, hashes e commits não aprovam conteúdo nem autorizam publicação.

## Ciclo padrão

1. Identificar branch/base, estado local, PRs relacionados e última evidência válida.
2. Classificar escopo, prioridade, risco, dependências e critérios de aceite.
3. Preservar alterações existentes antes de editar.
4. Corrigir e sanitizar somente o necessário, reutilizando componentes existentes.
5. Executar testes focados e registrar comandos, ambiente, resultados, falhas e limites.
6. Criar commit coerente com mensagem clara.
7. Encaminhar para revisão e integração na base correta, sem merge implícito.
8. Registrar estado final, evidências, pendências, impacto e próxima ação.

## Regra de execução e economia de Actions

GitHub Actions não é executor padrão de auditorias, testes ou provas pontuais. Não disparar workflows apenas para obter um selo de validação. Preferir execução focada no ambiente de desenvolvimento já disponível, sem criar serviços pagos ou consumir franquias adicionais sem necessidade comprovada. Se a execução depender de SSH Hostinger/OpenCode, registrar o comando e exigir retorno real; não afirmar que o teste foi executado pelo GitHub. Exceções operacionais já existentes só devem ser alteradas após substituto comprovado e avaliação de risco.

## Estados e marcos

| Estado | Significado | Próxima ação |
|---|---|---|
| PRONTO_PARA_COMMIT | Alteração concluída e validada no escopo | Criar commit |
| COMMITADO | Commit criado, ainda não integrado | Revisar e encaminhar integração |
| EM_REVISAO | PR aberto com pontos objetivos pendentes | Resolver os pontos |
| PRONTO_PARA_INTEGRAR | Critérios satisfeitos e autorização aplicável confirmada | Integrar |
| INTEGRADO | Commit incorporado à base indicada | Verificar estado resultante |
| BLOQUEADO | Impedimento concreto registrado | Continuar itens independentes |
| OBSOLETO | Duplicado ou sem finalidade atual | Encerrar com justificativa |

Não usar “concluído” como sinônimo de commitado, integrado ou implantado.

## Salvaguardas

- Preservar produção, dados, segredos, Gate, direitos de mídia e aprovações editoriais.
- Nenhum teste, hash, commit, PR aprovado ou autorização genérica de engenharia concede permissão para publicar, implantar ou escrever em sistemas externos.
- Não fazer merge automaticamente para reduzir o número de PRs.
- Não descartar alterações locais, reescrever histórico compartilhado, forçar push ou apagar branches para “limpar” o projeto.
- Não ativar executor autônomo, cron, workflow ou serviço externo por inferência documental.
- A política reduz acúmulo e estagnação; não elimina revisão humana em mudanças de risco.

## Indicadores mínimos

Acompanhar sem criar métricas artificiais: alterações prontas sem commit; commits aguardando integração e motivo; PRs sem próximo passo; bloqueios; falhas preexistentes versus regressões; e sanitizações realizadas com evidência.

A meta é reduzir continuamente o trabalho concluído porém não integrado, sem aumentar risco operacional nem burocracia.
