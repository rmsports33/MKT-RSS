# Conexo OS — saneamento pós-bloqueio de faturamento Actions
Data: 2026-11-02. Escopo: levantamento dirigido e plano de limpeza, sem alterar workflows, credenciais, WordPress ou publicadores.

## Verificações diretas
- GitHub Actions do projeto MKT-RSS funciona: PR #37 teve CI pytest, gate editorial e geração de artefato aprovados no SHA 1c51e48; https://github.com/rmsports33/MKT-RSS/actions/runs/41532586084.
- GitHub Actions privado do site foi reativado seletivamente e PRs #56 e #57 foram integrados anteriormente, com limites de concorrência e lint validado.
- Site `-site-conexotech` possui 29 definições de workflow em `.github/workflows/` (não significa que todas estejam habilitadas ou disparando). Incluem cron/rotinas, backup, watchdogs, preços, Telegram, espelho GitLab, deploy de tema e RSS. Estado habilitado e gatilhos de cada workflow precisam ser conferidos antes de limpeza; um arquivo YAML não comprova atividade.
- PRs MKT-RSS #33/#34/#35/#37 são drafts. #34 não está mergeable. Conexo OS #42 draft. Site #52 draft e dependente do #46. Não há prova de MU-plugin instalado e homologado no WordPress.
- O WordPress conectado por Jetpack permite leitura do rascunho #9711 e mídia #9714. A descrição da API também oferece posts.create(status=draft) e posts.get(context=edit) para readback; **não foi realizada escrita de teste**.

## Diagnóstico por prioridade
### Remover exigências do caminho crítico offline
1. Não exigir GitHub Actions, computador local ligado, Powershell, FTPS/SFTP ou DNS do terminal para geração Markdown/JSON -> HTML. Actions deve ser uma opção de CI e de distribuição do artefato; execução manual do Python permanece equivalente.
2. Não exigir API de modelo, OpenRouter/Groq, crawler SEO externo, banco remoto nem runner para receber artigo já redigido pelo ChatGPT ou humano.
3. Não exigir MU-plugin, assinatura, nonce e múltiplos gates independentes para *gerar e revisar prévia offline*. Essas exigências pertencem ao caminho de **escrita remota automatizada**, não ao renderizador.
4. Não tornar falta de exatamente 3 links ou metadescrição fora de intervalo preferido motivo de bloqueio da prévia. Registrar aviso e resolver antes da aprovação, quando aplicável.
5. Evitar que `status_validacao=PASS`, `review.approved=true`, resposta vazia do validador ou CI verde sejam confundidos com certificação factual ou autorização remota.

### Preservar, mas simplificar
6. Manter uma fonte canônica de contrato editorial e uma etapa de revisão humana por artigo. Relatório consultivo com fontes/claims e marcas de pendência é suficiente para homologação offline.
7. Manter limite de concorrência em CI; GitHub documenta grupos por workflow/ref e cancelamento apenas de jobs substituíveis: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
8. Consolidar testes direcionados por arquivo para desenvolvimento e suíte integral nas alterações relevantes e na integração final. Não deixar 3 ou mais pipelines redundantes testarem o mesmo commit sem motivação.
9. Manter bloqueio de publicação não autorizada, verificação de permissões, readback, idempotência e procedimento de recuperação no caminho remoto; evitar novas camadas sem caso de ameaça específico.

### Revisar e aposentar após confirmar necessidade
10. Auditar individualmente `auto-deploy.yml`, `deploy-tema.yml`, `deploy-telegram-primary.yml`, `espelho-gitlab.yml`, `verificar-assistente-telegram.yml`, `captura-diaria.yml`, `frescor-precos.yml`, `token_verification.yml`, `guardiao-opencode.yml`, `codespace-health.yml`, `verifica-nuvem.yml` e demais cron/guardas. Classificar: essencial/duplicado/aposentável/manual. Não religar serviços abandonados nem remover workflows sem revisar gatilhos e dependentes.
11. Inventariar endpoints, webhooks e segredos de Telegram/FTPS/Codex temporários e aposentá-los somente após confirmar consumidores e reversão. Não inspecionar ou exportar valores de segredos.
12. Fechar ou declarar obsoletos PRs experimentais sobrepostos (#36 opcional, #38 ponte já incorporada ao #37), **somente após** confirmar diff e preservar histórico. Não fazer merges de #34/#42 conflitantes.
13. Não converter automaticamente rotinas de produção em cron frequente: definir teto de minutos, regras de concorrência e acompanhamento de faturamento por repositório.
14. Depois que o pipeline estável estiver integrado, atualizar documentação que descreve soluções provisórias como obrigatórias e consolidar um único procedimento cloud-first.

## WordPress: homologação proporcional
- Marco A: pacote offline gera HTML de prévia + HTML fragmento + relatório sem escrever no WP — comprovado no PR #37.
- Marco B1: inspecionar schema da API, papel do usuário, post draft #9711, mídia #9714 e SEO registrável, comparar mapeamento do exportador sem escrita. Leitura realizada; não prova operação de save.
- Marco B2: uma escrita supervisionada com novo rascunho explicitamente autorizado, sem publicação e com idempotência por ID, readback e revisão visual em desktop/celular. Exige controle contra duplicatas e identidade apropriada; conta conectada pode atribuir autor ao usuário autenticado.
- Marco B3: publicação e automação assinada são etapas distintas; não exigir antes do primeiro draft supervisionado, mas não liberar publicação automática sem homologação real.
- Nenhum status do CI equivale à homologação do WordPress real.

## Contrato de evidências
- O adaptador existente `normalizar_snapshot_editorial/avaliar_snapshot_editorial` valida estrutura de EditorialContract 1.0 e não certifica veracidade.
- O núcleo do PR #37 agora emite `rastreabilidade_claims`, `fontes_sem_vinculo_canonico`, `revisao_factual_humana_pendente` e `aprovacao_publicacao=false`.
- O pacote #9711 possui 5 fontes resumidas em JSON, mas `claims=[]` e snapshot canônico ausente. A ausência é uma pendência factual real, **não um bloqueio para gerar a prévia**.
- Próxima etapa factual: coletar capturas/trechos datados, associar cada afirmação significativa ao ID da fonte e confirmar cobertura com revisão humana. Não fabricar status PASS.

## Resumo operacional
**Pode funcionar agora:** coleta/seleção manual de pautas, redação ChatGPT, exportação Markdown/JSON, SEO consultivo, HTML offline, testes e revisão.
**Ainda precisa homologar:** vínculo factual completo do Android Drop, escrita em draft supervisionada e readback, tema desktop/celular, gate e assinatura remota, cron/autopublicação.
**Nunca executar como efeito colateral deste saneamento:** publicar, instalar MU-plugin, expor secrets, religar automações de deploy ou alterar permissões.
