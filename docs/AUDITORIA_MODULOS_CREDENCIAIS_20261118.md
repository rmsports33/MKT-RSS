<!-- Status consolidado: docs/REGISTRO_UNICO_20261118.md -->

# Auditoria de mÃ³dulos desligados e credenciais â€” 18/11/2026

## MÃ³dulos relevantes desligados ou desconectados

| Item | Estado | Uso possÃ­vel |
|---|---|---|
| `conexo-gate-agenda-nativa` 0.3.3 | inativo | **NÃ£o ativar**: declara `cxgna_ready()` jÃ¡ existente no plugin ativo e causa erro fatal. CÃ³digo legado duplicado |
| `conexo-editorial-gate` 0.1.0-rc10.4 | ativo | Ã‰ o Gate real. Recebeu a trava de proveniÃªncia nesta auditoria |
| Review em vÃ­deo (`sugerir_video`, `render`) | desconectado do motor | Portado para `mkt_flow_p0/editorial_video.py`; exige curadoria humana |
| Capa Unsplash | fluxo parado | `UNSPLASH_ACCESS_KEY` existe nos secrets do MKT-RSS |
| `CONEXO_GATE_REMEDIATION_AUTO` | opt-in off | Pode corrigir descriÃ§Ãµes SEO dos 37 rascunhos antigos |
| Gate de valor M04.16D | opt-in off | Bloqueia preÃ§o sem evidÃªncia datada |
| PublicaÃ§Ã£o de comparativos | opt-in off | NÃºcleo do nicho do site |
| `CONEXO_RSS_CRON_ACTIVE=0` | off | Coleta sÃ³ por disparo manual (intencional) |
| `CONEXO_ACTIONS_WRITER_DISABLED` | era `0` | Ajustado para **1**, conforme a polÃ­tica de nÃ£o usar Actions como executor |

## Credenciais (somente nomes/estado â€” nenhum valor foi exibido)

| Origem | Achado |
|---|---|
| `~/.config/conexo-os/` | 9 arquivos, `600`; um `.uuid` com `644` (nÃ£o Ã© segredo) |
| Turso ro/rw antigos | expiravam em 20/11 â€” **rotacionados** |
| Novos tokens Turso | vÃ¡lidos, leitura confirmada na fila (24 pautas) |
| LimitaÃ§Ã£o | a API criou os dois tokens com permissÃ£o `rw`; nÃ£o foi possÃ­vel gerar um `ro` escopo restrito por esta via â€” pendente de criaÃ§Ã£o no painel Turso |
| WordPress ID4 | 6 Application Passwords; `bot.editor` e `MCP-PC` sem uso desde setembro; `Draft Writer` nunca usada; `Engine` em uso |
| GitHub MKT-RSS | 13 secrets (Groq, Turso, WP, Unsplash, EXA, Jina, Sheets, Telegram) |
| GitHub site | 36 secrets, incluindo `YOUTUBE_API_KEY`, `WP_USER_ADMIN`, FTP/SFTP, Hostinger, Drive, Notion, OpenCode |
| GitHub painel | 0 secrets |
| `.env` locais | nenhum; no servidor sÃ³ `.env.example` |
| Ausente | `CONEXO_EDITORIAL_GATE_KEY` â€” SEO nativo assinado segue indisponÃ­vel |

## Executado nesta auditoria

1. **Trava de proveniÃªncia implantada no Gate ativo**: `conexo-editorial-gate/includes/conexo-review-publisher.php`
   recebeu a checagem do manifesto. `php -l` sem erros. VerificaÃ§Ã£o real via
   WP-CLI nos posts 9900 e 9906: nenhum deles aparece como "Pacote editorial
   ausente"; aparecem honestamente `Identidade editorial nÃ£o aplicada`,
   `AvaliaÃ§Ã£o substantiva pendente`, `Direitos de imagem nÃ£o confirmados`.
2. Plugin legado `conexo-gate-agenda-nativa` restaurado ao original e mantido
   inativo (a tentativa de ativaÃ§Ã£o gerou erro fatal por duplicaÃ§Ã£o de funÃ§Ã£o).
3. Tokens Turso rotacionados; `rss-queue.env` atualizado; leitura confirmada.
4. `CONEXO_ACTIONS_WRITER_DISABLED=1`.
5. MÃ³dulo de vÃ­deo portado para o motor, com regras da polÃ­tica de curadoria e
   5 testes (134 testes passaram no conjunto de fronteira/proveniÃªncia/vÃ­deo).

## Pendente (nÃ£o executado por exigir decisÃ£o ou segredo humano)

- gerar token Turso **somente leitura** no painel;
- copiar `YOUTUBE_API_KEY` e `UNSPLASH_ACCESS_KEY` para arquivos privados no
  servidor e escolher 1 vÃ­deo aprovado pelos 5 critÃ©rios;
- habilitar remediaÃ§Ã£o automÃ¡tica e gate de valor apenas sob decisÃ£o explÃ­cita;
- publicar comparativos (opt-in) â€” altera comportamento editorial.
