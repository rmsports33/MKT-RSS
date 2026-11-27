# Inventário de uso de credenciais — 27/11/2026

Somente **nomes de variáveis**, serviços e referências. Nenhum valor é registrado.

## Serviços e variáveis

| Serviço | Nomes de variáveis | Onde aparecem (resumo) |
|---|---|---|
| WordPress | `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` | workflows em `-site-conexotech`, `site-conexotech`, `site-conexotech-editorial-gate`; documentação operacional; `mkt_flow_p0/wp_publisher.py`, `wp_draft_staging.py`, `wp_quality_executor.py` |
| Groq | `GROQ_API_KEY` | workflows RSS/homologação; `.env` local (fora do versionamento); `mkt_flow_p0/rewriter.py`, `provider_budget.py`, `editorial_development.py` |
| OpenRouter | `OPENROUTER_API_KEY` | `redator-artigo-blogs/src/evergreen.py`, `bot-redator-artigo/src/evergreen.py`, testes, ferramentas antigas de diagnóstico nos clones do site |
| Turso | `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | documentação operacional, `mkt_flow_p0/cloud_db.py`, probes |
| Gate V1 | `CONEXO_EDITORIAL_GATE_KEY`, `CONEXO_REVIEW_REGISTRY_KEY` | `gate_v1_registry_route.php`, `review_keys.py`, documentos de patch/evidência, testes de registro |
| Imagens | `UNSPLASH_ACCESS_KEY`, `PIXABAY_API_KEY` | `image_handler.py`, `stock_media_multi_source.py`, testes |
| Núcleo privado | `CONEXO_CORE_READ_TOKEN` | `.github/workflows/ci.yml` (somente leitura, opcional) |

## Exposição já identificada

- `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md`: chave OpenRouter, Application Password WordPress e senha de conta WordPress.
- A redação existe no commit `418be35` da branch do PR #6, **mas não é ancestral de `main` e é parcial**.
- Os commits de 23/09/2026 (`ac82ef13`, `86952ca5`) permanecem no histórico. Histórico **não** foi reescrito e nenhuma reescrita é autorizada nesta etapa.
- Remover texto não resolve exposição: a rotação depende de confirmação do proprietário nas contas externas.

## Estado documentado da rotação

| Credencial | Estado com evidência documental | Evidência |
|---|---|---|
| Groq (chave antiga da sessão) | revogada | `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md:46` |
| Application Password WordPress antiga | revogada/expirada (401) | `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md:48,148,269` |
| Outra Application Password exposta em chat | pendente de rotação pelo proprietário | `site-conexotech-editorial-gate/docs/memoria/2026-09.md:1428` |
| Senha da conta WordPress antiga | pendente de rotação | `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md:49` |
| OpenRouter | pendente / evidência conflitante | `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md:47`; `site-conexotech-editorial-gate/docs/memoria/2026-09.md:803-807` |
| Token da API Hostinger | rotacionado em 11/10, antigo revogado | `site-conexotech-editorial-gate/docs/PENDENCIAS_2026-10-10.md:247-257` |
| Token antigo do bot Telegram | revogado no BotFather | `site-conexotech-editorial-gate/docs/memoria/2026-09.md:797` |
| `GITHUB_TOKEN` / `TOKEN_TAP_GITHUB`, `EXA_API_KEY` | divergência não reconciliada; decisão do proprietário | `site-conexotech-editorial-gate/MEMORIA.md:4929-4940` |
| `POLLINATIONS_API_KEY` | removida do `.env` local; rotação não documentada | esta seção |
| `CONEXO_EDITORIAL_GATE_KEY`, `CONEXO_REVIEW_REGISTRY_KEY`, Turso, Groq atual, `WP_*` atual | sem evidência de exposição ou rotação nos documentos consultados | ausência de registro |

`CONEXO_EDITORIAL_GATE_KEY` e `CONEXO_REVIEW_REGISTRY_KEY` são pendências de **provisionamento**, não de rotação, e devem ser tratadas em fila separada. As chaves do Gate devem ser distintas entre si.

## Procedimento de rotação — execução do proprietário

Para cada credencial, **nesta ordem**:

1. Revogar/invalidar o valor antigo no provedor (WordPress, Groq, OpenRouter, Turso, Hostinger, Telegram ou outro).
2. Gerar valor novo no provedor, com escopo mínimo e sem compartilhar em canal de texto.
3. Atualizar **todos** os pontos de consumo: segredos de CI, `.env` local fora do Git, variáveis do terminal Hostinger e, quando aplicável, constantes ou opções do WordPress fora do repositório.
4. No Gate V1, atualizar apenas o que estiver fora do repositório: a opção `cxrm_authorized_service_user_id`, o UUID autorizado `cxrm_authorized_application_password_uuid` e as chaves de registro. **Não ativar as constantes de remediação** sem autorização específica.
5. Registrar neste documento a data e a confirmação do proprietário, **sem o valor**.
6. Não reescrever histórico Git e não fazer force push.

## Consumers e mudança de código

- A maioria das credenciais é lida em tempo de execução por `os.getenv` ou `getenv`; **trocar o valor não exige código**.
- Exige ajuste fora do valor: trocar o **nome** da variável, a identidade canônica do publicador (`conexo-mkt-rss`) ou o UUID autorizado no Gate.
- Existem duas famílias de variáveis WordPress (`WP_*` e `CONEXO_WP_*`); a rotação não deve misturá-las.
- `ops/hostinger/run_rss_queue.sh` rejeita `WP_USER`/`WP_APP_PASSWORD`: é escritor de fila, não publicador.
- `MKTFLOW/site/bancada.html` pede a Application Password por `prompt` e a mantém só em memória da aba; trocar a senha não exige código, trocar o usuário exige.
- Valores em testes, workflows e placeholders são sintéticos e **não** entram nesta rotação.

## Observações

- Nenhuma credencial de produção foi usada nesta operação.
- Nenhuma configuração de produção foi alterada.
- Não foi feita reescrita de histórico Git.
- As rotas de remediação do Gate V1 permanecem bloqueadas por padrão; nenhuma constante, UUID ou opção foi provisionada.
