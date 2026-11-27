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

## Exposição já identificada e tratada

- `bot-redator-artigo/SESSAO_2026-09-22_MEMORIA.md`: chave OpenRouter, Application Password WordPress e senha de conta WordPress. Redigidas no commit `418be35` da branch do PR #6.
- Dois commits de 23/09/2026 (`ac82ef13`, `86952ca5`) ainda contêm os valores no histórico Git. Histórico **não** foi reescrito.
- A remoção do texto não resolve a exposição: rotação das credenciais ainda pendente de confirmação do proprietário.

## Observações

- `POLLINATIONS_API_KEY` foi removida do `.env` local em execução anterior e não aparece no inventário versionado.
- Nenhuma credencial de produção foi usada nesta execução.
- Nenhuma configuração de produção foi alterada.
