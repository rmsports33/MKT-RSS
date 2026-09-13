# Publicar landings na Vercel (item 10) — grátis

As landings (`landing_<id>.html`) são páginas estáticas: hosting ideal é a
Vercel, não o WordPress. O `vercel.json` da raiz já deixa URLs limpas.

## Passo a passo (10 min, só cliques)

1. Conta em `vercel.com` (pode entrar com o GitHub).
2. No PC, crie a pasta `public/` dentro do projeto e copie pra ela os
   `landing_*.html` que quiser publicar + um `index.html` simples com links.
   Comandos prontos (Prompt de Comando, na pasta do projeto):
   ```
   cd "C:\Users\LIVE2PC\Desktop\MY PROJECTS FLOW"
   mkdir public
   copy landing_*.html public\
   ```
3. No painel da Vercel: Add New → Project → Import (suba a pasta `public`)
   ou conecte o repo e defina Output Directory = `public`.
4. Deploy → endereço `https://seu-projeto.vercel.app/landing_<id>`.

## Quando automatizar
Só vale o deploy automático (Action) quando houver volume (10+/semana).
Até lá, deploy manual mensal basta — landing de afiliado não expira rápido
(preço/estoque revalidam via pipeline, não via página).

# Backup no Google Drive (item 11)

## Primeira vez (5 min, com navegador)

1. `console.cloud.google.com` → crie projeto → ative **Google Drive API**.
2. Credenciais → Create Credentials → OAuth client ID → Desktop app.
   Baixe o JSON e salve como `credentials.json` na pasta do projeto
   (nunca commitar — já está no `.gitignore`).
3. No `.env`, preencha `GOOGLE_DRIVE_CLIENT_ID` e `GOOGLE_DRIVE_CLIENT_SECRET`.
4. Rode (abre o navegador 1 vez para autorizar):
   ```
   cd "C:\Users\LIVE2PC\Desktop\MY PROJECTS FLOW"
   python backup_drive.py
   ```
   Gera `mktflow-backup-<data>.zip` e sobe para a pasta `MKT-Flow-Backup`
   no Drive. Depois, `token.json` renova sozinho — próximos backups são
   1 comando (dá pra agendar no cron do Actions depois).
