# Checkpoint editorial — 2026-11-14 — Hostinger / Binance

## Evidências confirmadas
- Executor: `~/mkt-rss-runner`, Python 3.11; Gate autenticado e leitura com senha de aplicativo privada `~/.config/conexo-os/wp-editorial.token`.
- Post #9708: alteração de resumo SEO confirmada na fila do Gate; quatro pendências de imagem preservadas; nenhuma aprovação/publicação.
- Pacote criado: `~/.local/share/conexo-os/handoffs/rss_3fdd8256de5696d1869a36e8-108539d4b3737797.json`.
- 773 palavras no recibo, 1 fonte no pacote, 0 claims rastreados; estado `PENDING_HUMAN_REVIEW`, `wordpress_written` não foi verificado no arquivo completo; CLI relatou `escreveu=false`.
- Groq `openai/gpt-oss-120b`: geração 200 OK; revisão substantiva 429 PROVIDER_RATE_LIMIT; sem revisão independente, sem autorização factual.
- Enriquecimento e licença de imagem pendentes. Não regenerar o artigo apenas para contornar 429.

## Reconciliação factual para revisão humana
- Tecnoblog (14/11/2026) noticia que Binance **afirma 100% de cobertura** do prejuízo de cerca de US$ 6,3 bi: https://tecnoblog.net/noticias/r-34-bilhoes-binance-cobriu-100-do-prejuizo-do-maior-roubo-de-cripto-da-historia/
- Reuters (14/11/2026) relata **95% de cobertura** e retiradas parcialmente restabelecidas: https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/
- Reuters (31/10/2026) dizia cerca de US$ 6 bi de US$ 6,3 bi, ainda incompletos: https://www.reuters.com/legal/government/binance-says-90-stolen-assets-replenished-2026-10-31/
- AP (13/11/2026) registrou medidas de apreensão/congelamento de ativos; isso não equivale a cobertura de saldos: https://apnews.com/article/41be4834083e596a8facfd719f851cae
- É necessário verificar a hora e o escopo de cada declaração, distinguindo **recursos reservados**, **reposição efetiva de saldos**, **ativos congelados/recuperados** e **garantia 1:1**. Não afirmar que 100% foram recuperados.
- Texto original gerado no armazenamento privado do executor; metadados foram apresentados no chat, mas a revisão integral do `markdown` ainda não foi concluída. Não atribuir conteúdo não inspecionado ao artigo.

## Operação segura implementada
- `ops/hostinger/conexo_editorial.sh --inspect`: relatório local do último pacote, sem rede/escrita.
- `ops/hostinger/conexo_editorial.sh --handoff-one`: geração **manual e explícita** de um único pacote usando Groq privado; nunca roda WordPress/Turso. Evitar enquanto revisão factual de Binance estiver pendente ou houver limitação Groq.
- Nenhum cron novo, Actions, deploy ou publicação.
- O gancho pós-rascunho para correção SEO existe em `mkt_flow_p0/wp_draft_staging.py`, mas só executa após um rascunho confirmado e com `CONEXO_GATE_REMEDIATION_AUTO=1`. Não habilitar no coletor `run_rss_queue.sh` (queue-only).
- **Pendente para integração ponta a ponta:** pacote revisado com multifontes e evidências, imagem licenciada + revisão 390/1440 px, execução manual de rascunho pela rota editorial correta e confirmação do Gate. Essas etapas não foram executadas no servidor por esta conexão GitHub, que não fornece comandos SSH remotos.

## Próximo comando Hostinger, só leitura
```bash
cd ~/mkt-rss-runner
git pull --ff-only origin feat/hostinger-runtime-independente-20261113
bash ops/hostinger/conexo_editorial.sh --inspect
```
