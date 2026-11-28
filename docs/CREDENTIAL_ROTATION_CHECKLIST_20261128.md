# Checklist individual de rotação de credenciais — 28/11/2026

Finalidade: acompanhar a rotação feita **pelo proprietário nos painéis dos provedores**.
Nenhum valor secreto é enviado ao ChatGPT, ao OpenCode, ao GitHub ou registrado aqui.

Regras: revogar o valor antigo antes de criar o novo; atualizar todos os consumidores; testar autenticação; registrar apenas serviço, data, estado e responsável; não reescrever histórico Git.

Fonte: `docs/CREDENTIAL_USAGE_INVENTORY_20261127.md`.

## Rotação — execução do proprietário

| # | Serviço / credencial | Estado conhecido | Consumidores a atualizar | Serviço | Data | Estado | Responsável |
|---|---|---|---|---|---|---|---|
| 1 | WordPress — Application Passwords expostas | uma revogada; outra pendente | `.env`, cofre de CI, variáveis do executor, Gate (UUID) | — | — | pendente | proprietário |
| 2 | WordPress — senha de conta antiga | pendente | painel WP; não é lida pelo código | — | — | pendente | proprietário |
| 3 | OpenRouter — chave exposta | pendente / evidência conflitante | `src/evergreen.py` no Bot e na cópia vendorizada, ferramentas antigas | — | — | pendente | proprietário |
| 4 | Groq — chave antiga da sessão | revogada; atual sem registro | `rewriter.py`, `health_check.py`, cofre de CI | — | — | confirmar | proprietário |
| 5 | Turso — URL e token | sem registro de rotação | `cloud_db.py`, `editorial_trace_turso.py`, probes | — | — | pendente | proprietário |
| 6 | Hostinger — token da API | rotacionado em 11/10 | terminal Hostinger, integrações | — | — | confirmar | proprietário |
| 7 | GitHub / GitLab — tokens | divergência não reconciliada | espelho,_automações locais | — | — | pendente | proprietário |
| 8 | Telegram — token antigo | revogado no BotFather | bot administrativo, webhook | — | — | confirmar | proprietário |
| 9 | Imagens e pesquisa — chaves | sem registro de rotação | `image_handler.py`, coletores | — | — | revisar | proprietário |
| 10 | `POLLINATIONS_API_KEY` | removida do `.env` local | nenhum consumidor ativo conhecido | — | — | confirmar | proprietário |

Preencher as quatro últimas colunas somente com confirmação real. Não copiar valores.

## Ajustes de consumidor depois da rotação

- A maioria das credenciais é lida em tempo de execução; **trocar o valor não exige código**.
- Não misturar as famílias `WP_*` e `CONEXO_WP_*`.
- `ops/hostinger/run_rss_queue.sh` rejeita `WP_USER`/`WP_APP_PASSWORD`: é escritor de fila, não publicador.
- `MKTFLOW/site/bancada.html` pede a Application Password por `prompt` e a mantém só na aba; trocar a senha não exige código, trocar o usuário exige.
- Se o **nome** da variável ou a identidade canônica do publicador mudar, aí sim é necessária alteração de configuração/código.

## Rotação ≠ provisionamento do Gate

As chaves `CONEXO_EDITORIAL_GATE_KEY` e `CONEXO_REVIEW_REGISTRY_KEY` e as opções de remediação **não entram nesta fila**. São provisionamento futuro, com autorização separada, na Etapa 6. As rotas de remediação permanecem bloqueadas.

## Estado da etapa

**NOT STARTED** — depende exclusivamente de ação do proprietário nas contas externas.
