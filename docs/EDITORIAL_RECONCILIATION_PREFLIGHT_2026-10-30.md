# Reconciliação do publicador editorial — 2026-10-30

Estado: PREPARAÇÃO SEGURA. NÃO HOMOLOGADO / NÃO IMPLANTAR.

## Referências fixadas

- PR #33 head `a38b159c17c3681ffb034bfe9b203cd27db82e85` (base deste branch)
- PR #34 head `73db9a074cbba5b14efe12b3e8b495f1c9f097bf`; sua base aponta para `a3fe347e846b5266285ac4eb73d7375dd0ed4e8c` (12 commits anteriores à #33)
- Conexo OS PR #42 head `b143a0fd21fa69d1ae8ffa01a8ee3a80862d99f1`
- Site PR #52 head `299ced92d4188f50388c641fe265861b4844e1f2` (dependência #46)

## Regras que devem sobreviver ao merge semântico

1. A certificação factual não pode ser inferida de flags autodeclaradas, estado RSS ou aprovação vencida.
2. Nunca usar REST/MCP direto como fallback de escrita editorial.
3. Cliente e servidor exigem pacote, hash, vínculo a versão/site/ator, assinatura, validade, nonce, controle de concorrência e readback.
4. A publicação/agendamento exige aprovação independente atual e referência da operação específica; stage apenas cria rascunho técnico privado.
5. Preservar os testes adicionados aos dois branches e comparar resultado das suítes completas em checkout com hashes confirmados, zero skips das integrações críticas.
6. Não ativar MU-plugin isoladamente: bloqueia wp-admin e scripts antigos sem o publicador assinado operacional.

## Arquivos de maior risco

`editorial_publish_gate.py`, `editorial_wordpress_readiness.py`, `pipeline_rss.py`, `mkt_flow_p0/wp_publisher.py`, `tests/test_editorial_publish_gate.py`, `tests/test_editorial_wordpress_readiness.py`, `tests/test_wp_publish_no_bypass.py`. A PR #33 também adicionou `editorial_publish_transition.py` e `tests/test_editorial_publish_transition.py`.

## Critérios de implantação

- Backup UpdraftPlus de 2026-10-30 14:43 aparece como concluído no painel, mas ainda falta exportar, conferir integridade e testar recuperação isolada.
- Chave `CONEXO_EDITORIAL_GATE_KEY` deve ser gerada e armazenada exclusivamente em canais secretos no servidor e executor, nunca commitada ou enviada em comentários.
- Homologar plugin com WordPress/Jetpack reais em ambiente isolado e testar rota assinada, recusas diretas REST/MCP/XML-RPC, cron, concorrência e reversão.
- Instalar exclusivamente `wp-content/mu-plugins/conexo-editorial-gate.php` após validação, preservando `hostinger-auto-updates.php` e `hostinger-preview-domain.php`.
- Sem merge, deploy, Actions, publicação ou alteração do servidor por este preflight.
