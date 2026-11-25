# Staging Hostinger descontinuado — 25/11/2026

## Decisão

O staging da Hostinger (`staging.conexotech.com.br`) foi **descontinuado e não será reativado**. Não criar subdomínio, site ou ambiente substituto na Hostinger.

## Verificação

Consulta à API da Hostinger (`hosting_websites_list-domains` e `hosting_websites_list`) confirmou:

- `conexotech.com.br`: `parked: []`, `subdomains: []`
- Busca por site `staging`: `total: 0`

Ou seja, `staging.conexotech.com.br` **não existe como ambiente configurado** — aparece apenas como string em código e documentos históricos.

## Consequência operacional

O ambiente GitHub `rss-homolog` é de **VALIDAÇÃO** (banco Turso de homologação, preflight Groq, handoff local). Ele **não possui destino WordPress**.

Qualquer modo que tente escrever no WordPress (`draft`, `publish`, `schedule`) deve falhar antes de qualquer chamada REST nesse ambiente.

## Referências históricas (não representam ambiente ativo)

Os seguintes arquivos citam o staging antigo apenas como registro histórico e não devem ser interpretados como configuração vigente:

- `mkt_flow_p0/wp_draft_staging.py` — `ALLOWED_SITES` (atualizado nesta correção)
- `docs/PROTOCOLO_RECUPERACAO_OPERACIONAL_20261105.md`
- `docs/EMERGENCY_RSS_DRAFT_HANDOFF_20261103.md`
- `docs/AUDITORIA_OPENCODE_NAVEGADOR_IMAGENS_20261125.md`
- `AGENTS.md` (flag `CONEXO_RSS_DRAFT_STAGING`)
- workflows com `CONEXO_RSS_DRAFT_STAGING: '0'` (flag inerte, mantida por compatibilidade)
