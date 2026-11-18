# Validação final do PR #127 — 18/11/2026

## Identificação do checkout

- Repositório: `rmsports33/MKT-RSS`
- PR: #127 — `fix/editorial-import-provenance-video-20261118`
- Checkout: `/home/u401421381/mkt-rss-pr127-67116a5` (cópia isolada)
- SHA testado: `67116a57e4e00561574ea398e6ff7b3976281275`
- SHA esperado: `67116a57e4e00561574ea398e6ff7b3976281275` — conferido
- Python: 3.11.18 (venv existente). Python 3.14.7 no Windows local não foi usado, para manter o ambiente das validações anteriores.
- O checkout operacional não foi tocado. Nenhum arquivo de código ou teste foi alterado nesta execução.

## Resultados executados

| Escopo | Resultado |
| --- | ---: |
| `test_android_drop_9711_processa_html_real_sem_wordpress` | 1 passed |
| `test_real_modules_generate_preview_body_seo_and_pending_diagnostics_without_network` | 1 passed |
| Quatro módulos focados (proveniência, vídeo, formatos e importação) | 120 passed |
| Bateria relevante completa | **288 passed, 0 failed, 10 subtests** |

As duas asserções históricas que exigiam a tag `<table>` sem atributos passaram após as correções, preservando as verificações de conteúdo. A execução confirma as correções no SHA testado.

## Evidência externa

Registro de execução publicado no comentário do PR:
https://github.com/rmsports33/MKT-RSS/pull/127#issuecomment-6986915272

## Conclusão e limites

- Os testes informados passaram no SHA exato acima.
- A validação ocorreu em checkout isolado e com Python 3.11.18.
- Não houve alteração de código/testes nesta execução.
- Esta evidência não autoriza nem executa merge, deploy, publicação, alteração no WordPress/Turso, Gate ou cron.
- O PR permanece sujeito à revisão e decisão explícita de integração.
