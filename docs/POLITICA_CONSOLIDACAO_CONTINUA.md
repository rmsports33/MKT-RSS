# Política de consolidação contínua e sanitização — MKT-RSS

**Decisão operacional: 18/11/2026.** Esta política aplica ao código, testes, documentação, branches e PRs do MKT-RSS. Complementa o `AGENTS.md`, o contrato editorial e os controles de publicação. Prevalecem sempre as decisões mais recentes do proprietário e as salvaguardas mais restritivas.

## Regras

1. Trabalho concluído e validado no escopo deve ser registrado em commit coerente. Não deixar correções prontas indefinidamente apenas em diretórios locais ou conversas.
2. Antes de trocar de branch, editar, rebasear ou limpar, identificar e preservar alterações modificadas, não rastreadas e ignoradas relevantes. Nunca sobrescrever trabalho do usuário ou de outro agente.
3. Toda branch/PR deve declarar objetivo, base, head/SHA, arquivos, dependências, testes, bloqueios e próxima ação. PR sem atividade deve ser concluído, encerrado com justificativa ou mantido explicitamente bloqueado.
4. Integrar mudanças à branch de desenvolvimento apropriada assim que revisão, testes e dependências permitirem. Não acumular melhorias independentes para formar lotes artificiais.
5. Commit, merge e deploy são marcos distintos. Esta política não autoriza escrita WordPress/Turso, publicação, agendamento, alteração de Gate, deploy ou produção.
6. Classificar pendências como PRONTO_PARA_COMMIT, COMMITADO, EM_REVISAO, PRONTO_PARA_INTEGRAR, INTEGRADO, BLOQUEADO ou OBSOLETO. Cada item deve ter destino e próxima ação.
7. Resolver dependências na ordem correta; bloqueio de uma frente não paralisa trabalho independente. Agrupar apenas mudanças tecnicamente coerentes.
8. Testar proporcionalmente ao risco: primeiro a fronteira afetada, depois a suíte pertinente quando necessário. Não repetir auditorias/suítes sem mudança de código, ambiente, evidência ou hipótese.
9. Separar falhas preexistentes de regressões novas por comparação com a base relevante. Não esconder falhas nem declarar PASS para testes não executados.
10. Sanitizar progressivamente no escopo: remover duplicações, código morto, caminhos obsoletos e inconsistências com baixo risco de regressão. Refatorações amplas exigem escopo e critérios próprios.
11. Atualizar documentação e contratos afetados. Registrar resultados reais, limites e evidências; documentação não substitui execução.
12. Fechar o ciclo com commit verificável, validações registradas, destino de integração, pendências e próxima ação. Se merge não for autorizado ou seguro, deixar a revisão preparada e indicar o impedimento concreto.
13. Manter a continuidade independente de agente/ferramenta. A fonte de verdade é o repositório e seus artefatos versionados, não a memória de uma IA ou computador pessoal.
14. Evitar burocracia: não criar Actions, workflows, issues, PRs, relatórios ou serviços redundantes. Respeitar a política de economia de Actions e custos do projeto.
15. Preservar Gate, autoria, direitos de mídia, aprovação humana por versão, credenciais e dados. Testes, hashes e commits nunca aprovam conteúdo nem autorizam publicação.

## Ciclo de trabalho

1. Identificar branch/base, estado local, PRs relacionados e última evidência válida.
2. Classificar escopo, risco, dependências e aceite.
3. Preservar mudanças existentes antes de editar.
4. Corrigir e sanitizar somente o escopo necessário, reutilizando componentes existentes.
5. Executar testes focados e registrar resultado, falhas e limites.
6. Criar commit com mensagem clara.
7. Encaminhar para integração na base correta, sem merge implícito.
8. Registrar conclusão, pendências e próxima ação.

## Regra específica de execução

A política de economia de GitHub Actions permanece vigente: não disparar workflows apenas para obter um selo de validação. Preferir execução focada no ambiente de desenvolvimento já disponível. Se a execução depender do SSH Hostinger/OpenCode, registrar o comando e exigir retorno real; não afirmar que o teste foi executado pelo GitHub.

## Estados e marcos

Não usar “concluído” como sinônimo de commitado, integrado ou implantado. Registrar separadamente:
- **PRONTO_PARA_COMMIT:** alteração validada no escopo, ainda não commitada.
- **COMMITADO:** commit criado, ainda não integrado.
- **EM_REVISAO:** PR aberto com pontos objetivos pendentes.
- **PRONTO_PARA_INTEGRAR:** critérios satisfeitos e autorização aplicável confirmada.
- **INTEGRADO:** commit incorporado à branch indicada.
- **BLOQUEADO:** impedimento concreto registrado; tarefas independentes continuam.
- **OBSOLETO:** duplicado ou sem finalidade, encerrado com justificativa.

Indicadores mínimos: alterações prontas sem commit; commits aguardando integração; PRs sem próximo passo; bloqueios; falhas preexistentes versus regressões; e sanitizações realizadas com evidência.
