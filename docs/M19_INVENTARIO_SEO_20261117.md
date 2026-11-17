# M19 — Inventário SEO somente leitura — 17/11/2026

Nenhuma alteração em produção. Rank Math permanece ativo.

## Resultados (HTTP via proxy, DNS OK)

| Verificação | Resultado |
|---|---|
| HTTP home/sitemap/robots | ✅ 200 |
| Title home | ❌ `ConexoTech -` (quebrado) |
| Meta description | ✅ presente |
| Canonical | ✅ `https://conexotech.com.br/` |
| OG tags | ✅ description, image, site_name, title, type, url, locale, image:secure_url |
| Twitter | ✅ card, description, image, title |
| noindex | ✅ ausente |
| Sitemap index | ✅ 5 filhos: post(30), page(8), review(6), comparativo(3), category(5) = 52 URLs |
| Schema home | ⚠️ 2 blocos: `@graph` (Person×1, 6 `@id`) + Organization |
| **Schema review A57** | ❌ Person×2, Rating×2, Review×2, **@id=0** (duplicação sem identificador) |

URL afetada: `https://conexotech.com.br/reviews/samsung-galaxy-a57-5g-vale-a-pena-em-2026/`

## Correção necessária (executar no WordPress — NÃO no MKT-RSS)

1. **Título da home**: corrigir no Rank Math → Titles & Meta → Homepage → Title.
   Usar `ConexoTech — Reviews independentes e comparativos de tecnologia`.
2. **Schema duplicado na review A57**: identificar o emissor (Rank Math vs tema vs plugin de review).
   - Verificar em WordPress → Rank Math → Schema → se há dois bloqueos de Review/Recipe ativos.
   - Verificar `functions.php` do tema por `add_action` que injeta JSON-LD.
   - Garantir `@id` único por entidade (ex: `#organization`, `#website`, `#review-a57`).
   - Manter UM emissor de Schema; não desativar Rank Math.
3. **Rollback**: antes de qualquer mudança, backup (M21) e registrar o HTML bruto anterior.

## Critério de homologação (ainda não atendido)
- [ ] Metadados únicos (título corrigido)
- [ ] Schema sem entidades repetidas `@id`
- [ ] Sitemap/robots preservados (✅ já)
- [ ] Contrato SEO assinado + readback (PR #58, repo privado — pendente)
- [ ] Integração tema/WordPress real
- [ ] Rollback executado e comprovado
- [ ] Estabilidade sem regressão

Rank Math continua responsável pela saída pública até que todos os critérios sejam comprovados.
