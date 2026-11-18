# Auditoria de módulos desligados e credenciais — 18/11/2026

## Módulos relevantes desligados ou desconectados

| Item | Estado | Uso possível |
|---|---|---|
| `conexo-gate-agenda-nativa` 0.3.3 | inativo | **Não ativar**: declara `cxgna_ready()` já existente no plugin ativo e causa erro fatal. Código legado duplicado |
| `conexo-editorial-gate` 0.1.0-rc10.4 | ativo | É o Gate real. Recebeu a trava de proveniência nesta auditoria |
| Review em vídeo (`sugerir_video`, `render`) | desconectado do motor | Portado para `mkt_flow_p0/editorial_video.py`; exige curadoria humana |
| Capa Unsplash | fluxo parado | `UNSPLASH_ACCESS_KEY` existe nos secrets do MKT-RSS |
| `CONEXO_GATE_REMEDIATION_AUTO` | opt-in off | Pode corrigir descrições SEO dos 37 rascunhos antigos |
| Gate de valor M04.16D | opt-in off | Bloqueia preço sem evidência datada |
| Publicação de comparativos | opt-in off | Núcleo do nicho do site |
| `CONEXO_RSS_CRON_ACTIVE=0` | off | Coleta só por disparo manual (intencional) |
| `CONEXO_ACTIONS_WRITER_DISABLED` | era `0` | Ajustado para **1**, conforme a política de não usar Actions como executor |

## Credenciais (somente nomes/estado — nenhum valor foi exibido)

| Origem | Achado |
|---|---|
| `~/.config/conexo-os/` | 9 arquivos, `600`; um `.uuid` com `644` (não é segredo) |
| Turso ro/rw antigos | expiravam em 20/11 — **rotacionados** |
| Novos tokens Turso | válidos, leitura confirmada na fila (24 pautas) |
| Limitação | a API criou os dois tokens com permissão `rw`; não foi possível gerar um `ro` escopo restrito por esta via — pendente de criação no painel Turso |
| WordPress ID4 | 6 Application Passwords; `bot.editor` e `MCP-PC` sem uso desde setembro; `Draft Writer` nunca usada; `Engine` em uso |
| GitHub MKT-RSS | 13 secrets (Groq, Turso, WP, Unsplash, EXA, Jina, Sheets, Telegram) |
| GitHub site | 36 secrets, incluindo `YOUTUBE_API_KEY`, `WP_USER_ADMIN`, FTP/SFTP, Hostinger, Drive, Notion, OpenCode |
| GitHub painel | 0 secrets |
| `.env` locais | nenhum; no servidor só `.env.example` |
| Ausente | `CONEXO_EDITORIAL_GATE_KEY` — SEO nativo assinado segue indisponível |

## Executado nesta auditoria

1. **Trava de proveniência implantada no Gate ativo**: `conexo-editorial-gate/includes/conexo-review-publisher.php`
   recebeu a checagem do manifesto. `php -l` sem erros. Verificação real via
   WP-CLI nos posts 9900 e 9906: nenhum deles aparece como "Pacote editorial
   ausente"; aparecem honestamente `Identidade editorial não aplicada`,
   `Avaliação substantiva pendente`, `Direitos de imagem não confirmados`.
2. Plugin legado `conexo-gate-agenda-nativa` restaurado ao original e mantido
   inativo (a tentativa de ativação gerou erro fatal por duplicação de função).
3. Tokens Turso rotacionados; `rss-queue.env` atualizado; leitura confirmada.
4. `CONEXO_ACTIONS_WRITER_DISABLED=1`.
5. Módulo de vídeo portado para o motor, com regras da política de curadoria e
   5 testes (134 testes passaram no conjunto de fronteira/proveniência/vídeo).

## Pendente (não executado por exigir decisão ou segredo humano)

- gerar token Turso **somente leitura** no painel;
- copiar `YOUTUBE_API_KEY` e `UNSPLASH_ACCESS_KEY` para arquivos privados no
  servidor e escolher 1 vídeo aprovado pelos 5 critérios;
- habilitar remediação automática e gate de valor apenas sob decisão explícita;
- publicar comparativos (opt-in) — altera comportamento editorial.
