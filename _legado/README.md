# MKTFLOW — congelado em `_legado/MKTFLOW` (12/09/2026)

Movido de `MKTFLOW/` para `_legado/MKTFLOW/` como parte do Plano de Estrutura (Bloco C).

## Status
- **Somente leitura.** Nenhum código novo aqui; referência histórica e suporte aos testes legados.
- Núcleo ativo: `mkt_flow_p0/` (22+ módulos, suíte verde, produção na nuvem).

## Por que não apagar
14 testes em `tests/legado/` ainda importam de `MKTFLOW.*`. Apagar quebraria a rede de segurança antes da migração completa (item 19 do roadmap).

## O que pode mudar
- Nada em `.py`. Remoção futura só após migração dos testes para `mkt_flow_p0/` (bloco dedicado).
- `venv/` (~500MB) continua aqui até confirmação de que ninguém usa o modo `pipeline.py` (Sheets).

## Como voltar (rollback)
`Move-Item _legado\MKTFLOW MKTFLOW` — sem perda, git guarda tudo.
