# Nuvem — tirar o pipeline do PC (grátis)

Objetivo: robô roda sozinho 1x/dia no GitHub Actions; PC serve só para
revisar rascunhos no WordPress. Custo: R$ 0.

## 1. Subir o código (uma vez)

1. Crie conta em `github.com` e um repositório **privado** (privado tem
   2000 min/mês grátis — nosso job usa ~90 min/mês).
2. No PC, dentro da pasta do projeto:
   ```
   git remote add origin https://github.com/SEU-USUARIO/mkt-flow.git
   git push -u origin master
   ```
   O `.gitignore` já barra `.env`, `*.db`, `token/credentials.json`.

## 2. Segredos (nunca no código)

Repo → Settings → Secrets and variables → Actions → New repository secret.
Crie um por um (valores estão no seu `.env` local):

| Secret | Obrigatório |
|---|---|
| `GROQ_API_KEY` | sim (reescrita) |
| `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` | sim (draft no WP) |
| `GROQ_MODEL` | não (default `llama-3.3-70b-versatile`) |
| `UNSPLASH_ACCESS_KEY` | não (só fallback de capa) |

## 3. Testar manual (antes de esperar o cron)

Repo → Actions → "RSS diario (WP draft)" → Run workflow → Run.
Verde = rascunhos caíram em Postagens → Rascunhos no WordPress.
O artefato `rss-runs-N` guarda o `mkt_flow_p0.db` do dia (14 dias).

## 4. Watchdog (grátis, 5 min)

O cron do Actions atrasa 5–15 min e pausa sem commits por 60 dias.
Contorno: conta grátis em `cron-job.org` → Create cronjob → URL:
`https://api.github.com/repos/SEU-USUARIO/mkt-flow/actions/workflows/daily.yml/dispatches`
método POST, header `Authorization: Bearer SEU_TOKEN` (token com escopo
`repo` → Settings do GitHub → Developer settings → Personal access tokens),
body `{"ref":"master"}`, 1x/dia às 09:05 BRT.

## 5. Limites conhecidos (sem surpresa)

- Runner é **efêmero**: `rss_vistos` (dedup) zera a cada run. Na prática,
  feeds tech giram rápido e `--limit 2` evita reprise; a correção definitiva
  é o item 9 (Turso) quando o volume justificar.
- Groq tier grátis tem rate limit: 429 → o `rewriter.py` já orienta esperar.
- Logs do Actions nunca mostram secrets (o GitHub mascara `***`).

## 6. Quando pagar (só com receita)

| Sinal | Ação |
|---|---|
| >2000 min/mês ou precisão de minuto | Railway/Render cron ~$5/mês (mesmo código) |
| Reprise de pauta entre dias | Turso free (5GB) no lugar do SQLite |
| Landings com tráfego | Vercel (deploy da pasta de HTML) |
