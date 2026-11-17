# Estado das frentes remanescentes — 16/11/2026

Registro factual do que está pendente e **por quê**. Nada aqui autoriza publicação,
deploy, exclusão de mídia ou alteração de gate. Serve para não repetir o problema
do recibo Binance (evidência perdida por não estar versionada).

## 1. Piloto SEO / resolução DNS — ⚠️ PENDENTE (externo)

- Não existe documento de DNS neste repositório; apenas `BROKER_SIGNED_SEO_20261108.md`
  e `relatorio-seo-ferramentas.md` (inventário, não homologação).
- Erro prévio registrado: `Temporary failure in name resolution`.
- **Bloqueio:** depende de rede/WordPress/DNS ao vivo, fora do alcance de execução local.
- **Para fechar:** executar preflight de SEO assinado contra `conexotech.com.br` com
  o signer oficial; registrar `seo-readiness` com `seo_key_mode` e
  `seo_key_proof` verificados. Sem recibo, não declarar SEO nativo homologado;
  Rank Math permanece ativo.

## 2. Imagens #9705 / #9708 — ⚠️ PARCIAL (depende de humano)

Fonte: `docs/IMAGE_GATE_AUDIT_2026-11-13_POST9705.md` (branch `feat/gate-editorial-unificado-20261116`).

- **#9705:** mídia antiga #9704 (`featured-60.jpg`, com branding 9to5Google)
  desvinculada; nova mídia #9888 (Fitbit Inspire 3, Tatsuo Yamashita, Wikimedia
  Commons, CC BY 4.0) associada, com autor/fonte/licença/alt. Post segue `draft`.
- **#9708:** preservado, bloqueado para revisão (mídia #9707 sem comprovação).
- Gate rc10.4 classifica pendências de mídia em `cxgna_draft_readiness()`,
  impedindo aprovação por falta de prontidão técnica.

**Homologação restante (NÃO CONCLUÍDA):**
1. Executar `tests/test_image_protocol.py` no checkout do executor (testes PHP locais
   não substituem).
2. Identificar Python 3.10+ no host e ligar o código ao processo real que cria
   drafts. O SSH mostrou Python 3.6.8; `~/mkt-rss-shopee-check` existe, mas sem
   comprovação de worker automático. Sem cron novo/ Actions/serviço pago.
3. Executar rascunho ponta a ponta com credencial MKT-RSS, manifesto licenciado,
   foto validada em 390/1440 e retorno ao Gate; checagem visual de capas suspeitas.
4. Somente com evidência verificável declarar automação de imagem concluída.

**Não fazer:** apagar imagens antigas em lote; inferir licença pelo nome do arquivo;
aprovar sem revisão substantiva do texto (#9705 reproduz estrutura de fonte de
terceiros).

## 3. Backups — ⚠️ SEM REGISTRO RECENTE

- Último checkpoint registrado: `ConexoOS-20261113-155214` (13/11/2026).
- `.github/workflows/backup.yml` existe mas só tem `workflow_dispatch` (manual),
  sem `schedule`/cron ativo.
- Não há registro de backup após 13/11 neste repositório.

**Para fechar:** executar backup verificável (UpdraftPlus já instalado no WordPress;
arquivos no Drive `/UpdraftPlus`), registrar data/ID do checkpoint econfirmar
readback. Não restaurar integralmente (decisão explícita do proprietário).

## Resumo

| Frente | Status | Natureza do bloqueio |
|--------|--------|----------------------|
| SEO/DNS | Pendente | Rede/WordPress ao vivo |
| Imagens #9705/#9708 | Parcial | Revisão visual + worker real no host |
| Backups | Sem registro recente | Execução no Drive/servidor |

Nenhuma frente foi concluída ou alterada por este registro. Master permanece
em `f021ea9d`; nenhum gate, publicação ou deploy foi modificado.

## Correções factuais (inventário cruzado 16/11)

Após cruzar as auditorias exportadas com o estado real do repositório:

| Afirmação em conversa anterior | Realidade verificada |
|---|---|
| PR #46 "plano operacional aberto" | **MERGED** em master (título: checar broker/Turso/prontidão SEO) |
| PR #58 "do MKT-RSS" | É do repo privado `-site-conexotech`, **draft**, base `fix/editorial-mcp-gate-c08e14d5` |
| "842 testes aprovados" | Número histórico; o checkout atual tem **161 arquivos de teste** |
| "Cron a cada 5 min" | Cron real: `* * * * *` (cada minuto); protegido por lock no controlador |
| "Python 3.6.8 é o runtime" | Python real do runner: **3.11.18** em `~/mkt-rss-runner/.venv` |
| WordPress MCP obrigatório | Não conectado nesta sessão; usar HTTP/SSH via operador |
| Shopee sincronizador "na operacional" | Está em `master`/FEAT; branch operacional **não** o contém |

## Triagem das 20 pautas — REGISTRADA

Ver `docs/TRIAGEM_DESCOBERTA_20261116.md`: 20 títulos `DESCOBERTA` priorizados
(4 alta, 8 média, 8 baixa/comercial) via ação `queue_list` (somente leitura).
Nenhuma pauta foi movida de estado; decisão editorial permanece com o proprietário.
