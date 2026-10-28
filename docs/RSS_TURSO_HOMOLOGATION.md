# Homologação Turso RSS — preparo seguro, sem execução automática

Banco isolado confirmado por captura no painel Turso: `mkt-rss-homolog` (organização `rmsports33`, plano Free mostrado no painel); banco principal `mkt-rss` não pode ser usado.

## Segurança e configuração

1. No painel Turso, gerar token **de banco individual** para `mkt-rss-homolog`, com escrita, nunca token do grupo ou da organização.
2. No GitHub, configurar **Environment** separado `rss-homolog`, restringindo a branch `feat/rss-editorial-queue-p0-20261026` e, idealmente, exigindo aprovação do mantenedor.
3. Salvar **somente nesse Environment** os secrets `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`. Nunca registrar token no chat, comentário, branch, output, artefato ou log. Verificar custo zero antes de gerar credencial.
4. A integração GitHub disponível nesta sessão **não pode criar ou consultar secrets nem iniciar um comando remoto**; portanto nenhuma credencial foi configurada aqui. Um executor na nuvem autorizado deverá montar essas variáveis exclusivamente no processo de teste, não em produção.

## Prova em duas execuções realmente independentes

A partir do checkout da branch, no executor cloud autorizado com as duas variáveis privadas definidas:

```bash
python -m scripts.rss_queue_turso_homolog_probe seed --case caso-aleatorio-unico
# Encerrar a tarefa/sessão de execução. Iniciar uma SEGUNDA execução cloud separada, com o mesmo case:
python -m scripts.rss_queue_turso_homolog_probe verify --case caso-aleatorio-unico
```

A ferramenta bloqueia qualquer hostname diferente de `mkt-rss-homolog-rmsports33.aws-ap-northeast-1.turso.io`. A primeira passagem deve inserir exatamente um registro sintético. A segunda deve confirmar a duplicata e persistência do mesmo ID. Nenhum RSS real, IA ou WordPress é acionado.

Para o teste de concorrência, usar **dois executores independentes** no mesmo banco de homologação, com casos adequados e coordenação, demonstrando uma falha fechada sob disputa e que nenhuma pauta duplicada foi criada. Não aceitar somente uma prova local com threads como equivalente. Não iniciar coleta paralela agendada antes da validação.

**Limite operacional:** um workflow novo de `workflow_dispatch` incluído só na branch do PR não fica normalmente disponível para disparo pela interface enquanto não existir na branch padrão. Portanto não foi criado workflow novo nem realizado merge para contornar essa restrição. Reutilizar executor cloud autorizado que ofereça variáveis de ambiente privadas ou aguardar decisão explícita sobre mecanismo de disparo.

## Critérios

- Plano continua gratuito e não há exigência de cartão.
- Duas execuções separadas retornam `seed new=true` e `verify duplicate=true persisted=true`, com IDs iguais.
- Dois executores não duplicam título equivalente e reserva de escrita é liberada apropriadamente.
- Os secrets permanecem inacessíveis a PRs públicos ou jobs não autorizados.
- Ao concluir, revogar token de homologação ou mantê-lo restrito conforme política, sem tocar em produção.

**Estado 27/10/2026:** script e testes de guarda preparados no PR #28. Instalação de secrets, duas execuções remotas e prova concorrente real permanecem pendentes e **não foram simuladas como concluídas**.
