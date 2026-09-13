# Embalagens do projeto — roadmap guardado (12/09/2026)

Decisão do usuário: revisitá-las **somente quando o projeto estiver maduro e eficiente**.
Gates de maturidade (todos precisam estar verdes para abrir esta discussão):
- [ ] Suite pytest verde ≥ 200 asserts, CI verde há 30 dias
- [ ] Cron diário verde ≥ 30 dias seguidos, dedup Turso ativo sem reprises
- [ ] ≥ 60 rascunhos aprovados/publicados com taxa de reescrita humana < 20%
- [ ] Custo médio/post medido (Groq) e abaixo de R$ 0,20
- [ ] Checklist de revisão formalizado e cumprido (fatos fortes checados)

## Opções mapeadas (não implementar antes dos gates)

### Fase 1 — validação com usuário real
1. **App Streamlit** ("cola URL → revisa → envia pro WP") — nota 9/10.
   Base existente: `MKTFLOW/app.py`. Hospedagem: share.streamlit.io (grátis).
2. **Template n8n** (RSS → Groq → WP) — nota 9/10.
   Usuário importa, cola 3 chaves e liga. Custo usuário: cloud pago ou self-host.

### Fase 2 — escala de curadoria
3. **Bot Telegram** (manda link, recebe rascunho) — nota 8/10.
   Requer hospedagem 24h (Railway/Render free dorme — validar antes).
4. **Extensão Chrome** (botão "vira rascunho") — nota 7/10.
   JS + backend nosso no ar; taxa Web Store ~US$5; manutenção em 2 linguagens.

### Fase 3 — com receita
5. **Plugin WordPress nativo** — nota 6/10.
   PHP × Python: ou reescreve motor em PHP ou plugin thin-client + backend
   hospedado. Só com recorrência que pague a manutenção.

## Comparativo registrado
| Embalagem | Iniciante? | Custo usuário | Esforço | Nota |
|---|---|---|---|---|
| Template n8n | sim | grátis~pago | baixo | 9/10 |
| App Streamlit | sim | grátis | baixo-médio | 9/10 |
| Bot Telegram | sim, muito | grátis* | médio | 8/10 |
| Extensão Chrome | sim | ~zero | médio-alto | 7/10 |
| Plugin WP | sim | zero | alto | 6/10 |
