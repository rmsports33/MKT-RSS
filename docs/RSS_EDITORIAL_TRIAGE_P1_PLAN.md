# P1 — Triagem editorial humana da fila RSS (plano, não implementação)

Data: 28/10/2026. Dependência: P0 homologada em `docs/RSS_EDITORIAL_QUEUE_P0.md`.

## Objetivo e limite

Permitir selecionar ou rejeitar conscientemente pautas já descobertas, **sem redigir, publicar, agendar, criar rascunhos WordPress ou mudar parâmetros de produção**. O banco `mkt-rss-homolog` é o ambiente de prova. O operador controla transições; nenhuma heurística muda status automaticamente.

## Contrato funcional mínimo

1. **Consulta somente leitura:** listar pautas com estado `DESCOBERTA` usando `listar(estado="DESCOBERTA", limite=...)` e apresentar ID, fonte, URL, título, estado e pontuação. A pontuação existente é calculada por palavras-chave; não é verificação de fatos, tendência, relevância comprovada ou aprovação editorial.
2. **Decisão explícita:** para cada ID escolhido, aceitar ação `selecionar` (mudar para `SELECIONADA`) ou `rejeitar` (`REJEITADA`). Exigir justificativa não vazia, identidade do operador e confirmação antes da gravação. Proibir operações em lote sem revisão individual.
3. **Controle de concorrência:** usar a atualização condicional existente em `mudar_estado`; conflitos devem falhar fechados, sem segundo update silencioso. Nenhuma alteração em `CONCLUIDA` ou `BLOQUEADA`.
4. **Rastreabilidade:** registrar decisão, justificativa, momento, ID da pauta e identidade operacional. Planejar armazenamento/auditoria consistente antes de implementar, não usar somente logs efêmeros como prova. Não incluir credenciais em logs.
5. **Interface:** primeiro protótipo em comando manual ou workflow `workflow_dispatch` com acesso mínimo; implementar em branch/PR separado com testes offline, sem acionar `rss-homolog-manual.yml` para editar estados. A implementação deve prever confirmação explícita do usuário para gravação.
6. **Segurança:** falha de Turso impede a operação, sem fallback SQLite. Verificar hostname do banco de homologação. Não ler/injetar secrets WordPress ou LLM. Não criar cron, webhook de publicação ou deploy.

## Critérios objetivos de aceite P1

- Listagem somente leitura de até 20 pautas, com metadados reais e indicação de que a pontuação é heurística.
- Seleção/rejeição individual com justificativa e auditoria recuperável, sem exposição de secrets.
- Testes negativos: ID inexistente, estado proibido, justificativa ausente, conflito de versão/estado, Turso sem credenciais, banco de produção, tentativa de execução sem confirmação.
- Testes positivos: operação em SQLite isolado e homologação controlada no Turso, preservando resultado entre dois jobs.
- CI aprovado e revisão do PR P1 antes de qualquer integração; homologação real não autoriza redação/publicação.
- **Não incluído nesta fase:** IA editorial, scraping de corpo completo, produção de artigo, rascunho WordPress, publicação, agendamento, autoprioridade e escala de workers.

## Estado e decisão

P0: encerrada no escopo de homologação manual, com execução #1 (3 novas/0 duplicadas) e #2 (0 novas/3 duplicadas), ambos com `falhas=[]`. P1: **planejada, não implementada nem autorizada para ativação**. Prioridade recomendada: criar uma branch P1 e testes offline antes de escrever quaisquer decisões no banco.
