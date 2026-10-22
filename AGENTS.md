# MKT-RSS — instruções operacionais para agentes (Jules, Aider e Codex)

## Objetivo
Entregar correções que permitam produzir rascunhos ConexoTech confiáveis, com o mínimo de tempo humano em comandos e relatórios. Medir entregas utilizáveis, não quantidade de testes.

## Coordenação Jules → GitHub → Aider
- GitHub é a fonte compartilhada: issues, branches, commits, PRs e estado verificável. Histórico de chats dos agentes NÃO é sincronizado.
- **Jules (nuvem)**: investigar e implementar defeitos de maior complexidade, numa branch isolada, entregando commits/PR com síntese das mudanças e bloqueios.
- **Aider (PC)**: após sincronizar a branch remotamente, realizar apenas ajustes locais, compatibilidade Windows e testes focados; trabalhar numa branch própria derivada da entrega Jules, nunca editar simultaneamente a mesma branch.
- **Conexo OS**: priorizar issues existentes e registrar somente entrega, prova de funcionamento e impedimento real. Não criar pipelines/agendadores adicionais para este piloto.
- Aider requer modelo de IA separado. Ollama local é uma possibilidade sem cobrança de API; a viabilidade depende do hardware do PC. Não pressupor Ollama/Aider já instalados.

## Critérios de execução
1. Ler o código e os testes pertinentes, reproduzir problema concreto e corrigir de forma simples.
2. Testes direcionados durante o trabalho; suíte integral uma vez antes de entregar alterações significativas.
3. Reportar somente: código entregue, testes efetivamente executados, limitações conhecidas e link do PR.
4. Nunca inventar testes práticos de produtos, preços, datas, specs, vídeos assistidos ou fontes. Ausência de alerta textual não significa verificação factual completa.
5. O WordPress recebe exclusivamente **rascunhos**; não publicar conteúdo público.
6. Não fazer merge, deploy de produção, alterar credenciais ou assumir custos sem autorização explícita.
7. Quando a tarefa não couber na capacidade do agente, sinalizar bloqueio real em vez de repetir diagnósticos e relatórios.
8. Evitar consumo desnecessário de GitHub Actions, tokens e tarefas gratuitas Jules.

## Piloto de integração
- Repositório: `rmsports33/MKT-RSS`
- PR de referência: https://github.com/rmsports33/MKT-RSS/pull/13
- Objetivo do piloto: resolver defeitos editoriais restantes e obter um artigo de exemplo fundamentado, **sem publicação**, para revisão humana.
- Não declarar o piloto concluído por quantidade de testes: exigir resultado editorial aproveitável.

## Pesquisa de ferramentas
Na avaliação de arquitetura ou surgimento de uma lacuna real, pesquisar alternativas online e registrar apenas proposta que tenha ganho concreto de capacidade/custo. Não interromper cada tarefa de código para pesquisar ferramentas redundantes.
