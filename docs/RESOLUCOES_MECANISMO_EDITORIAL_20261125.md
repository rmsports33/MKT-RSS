# RESOLUÇÕES DO MECANISMO EDITORIAL — 25/11/2026

**Escopo:** itens que podem ser resolvidos sem gravação no WordPress, sem
deploy, sem publicação e sem decisão do proprietário. Nada foi commitado.

---

## Itens resolvidos nesta sessão

| # | Problema | O que foi feito | Evidência |
|---|---|---|---|
| 1 | Origem não registrada | `editorial_import.py` aceita `authoring_provenance` (ferramenta, versão, hash de entrada). Ausência vira `NAO_REGISTRADA`; nunca infere modelo. Vai para o `result` e para o `trace`, nunca para o handoff. | `tests/test_editorial_import_provenance.py` (14 testes) |
| 4 | Sem avaliação substantiva do #9900 | Avaliação **assistida** (não humana, não do Gate), com 5 critérios, trechos literais e `status: PENDING`. Não virou PASS. | `docs/editorial-evidence/9900/assisted-substantive-assessment.json` |
| 5 | EXECUTED confundido com PASS | `execution_vs_approval` separa módulos executados de aprovados; só `PASS`/`PRONTO_PARA_REVISAO_HUMANA` contam como aprovados. Publicação continua `false`. | `tests/test_editorial_import_provenance.py` |
| 9 | Direitos de imagem ausentes do pacote | Novo campo `image_rights` com `confirmed`, `featured_media_id` e `evidence`. Confirmação continua dependendo do parâmetro explícito. | `tests/test_editorial_import_provenance.py` |
| 10 | Recibo não reproduzível | `verificar_recibo()` reconstrói a marca a partir do corpo. Aplicado ao #9900: hash confere, mas o Gate recusa por `voz_nao_aplicada` — ou seja, o problema nunca foi divergência de hash. | `tests/test_editorial_provenance_recibo.py`; `docs/editorial-evidence/9900/receipt-verification.json` |
| 12 | Reparo e lente MDA desconectados | `pipeline_rss.py` agora chama `reparar_paragrafos` **só quando há fragmentação detectada** e registra `verificar_voz_editorial_mda` como diagnóstico (`autoriza_publicacao: false`). | `tests/test_pipeline_reparo_mda.py` |
| 13 | Carimbo antigo sobrevivia à edição | `atualizar_handoff_revisao` invalida **qualquer** status de voz quando o Markdown muda, inclusive `PROMPT_APPLIED`. | `tests/test_editorial_prova_voz.py` (23 testes) |
| 12b | Construtores de prova inexistentes | Novas funções públicas: `construir_prova_voz_assistida`, `construir_prova_voz_humana`, `construir_prova_voz_externa`, todas validadas. | `tests/test_editorial_prova_voz.py` |
| Extra | Relatório de linguagem não serializava | `auditoria_linguagem` agora é convertido de dataclass para dict antes de entrar no resultado. Corrige 2 testes antigos que falhavam. | suíte consolidated |

## Testes

```
python -m pytest tests/test_editorial_prova_voz.py \
  tests/test_editorial_import_provenance.py \
  tests/test_pipeline_reparo_mda.py \
  tests/test_editorial_provenance_recibo.py \
  tests/test_editorial_readiness.py \
  tests/test_editorial_import_public.py \
  tests/test_editorial_handoff_operational.py \
  tests/test_editorial_substance.py -q

116 passed in 5.40s
```

Uma falha antiga e específica de Windows permanece fora deste escopo: um teste
espera permissão `0o600` num arquivo temporário, mas o sistema devolve `0o666`.
Não é problema de lógica editorial e não foi alterado.

---

## Itens que dependem de você

| # | Problema | O que só você pode decidir/fazer |
|---|---|---|
| 2 | Runtime parcial no servidor | Autorizar a instalação do código completo do motor no servidor. |
| 6 | HTML quebrado no #9900/#9906 | Autorizar a gravação do reparo nos rascunhos vivos. O código já está pronto. |
| 7 | Validador só alerta | Decidir se erros graves devem bloquear a gravação do rascunho. Hoje continua apenas sinalizando. |
| 8 | Fontes sem link | ✅ **Decidido:** pauta descartada por falta de documento oficial; #9900 na lixeira. #9906 segue disponível. |
| 11 | Nenhum parecer humano | Aprovar no Gate, escolhendo **"Aprovar e manter em espera"**. É o único ato que não posso fazer por você. |

## Decisões do proprietário executadas em 25/11/2026

| Decisão | Execução |
|---|---|
| 1 e 2 — consertar o texto e preparar as duas versões | #9900 corrigido (51 → 15 parágrafos; afirmações sem fonte reescritas; novo hash com readback exato). #9906 verificado: não precisava de reparo, permaneceu intacto. **Depois da revisão do proprietário, a pauta #9900 foi excluída** por falta de documentação oficial: post movido para lixeira, conteúdo preservado, hash inalterado. Evidências: `draft-repair-20261125.json` e `exclusion-20261125.json`. |
| 3 — link para análise | Enviado no chat: revisão e prévia dos dois posts, mais a fila do Gate. |
| 4 — rascunho oferecido já pronto | `pipeline_rss.py` agora repara o HTML **antes** de validar e **bloqueia** a gravação quando há erro crítico, de caractere ou estrutural. Heurísticas de estilo continuam só sinalizadas. |
| 5 — código completo no servidor | ⏸️ Aguardando informação: o proprietário pediu mais dados para decidir. |

Os textos continuam com `voice_status: NOT_APPLIED` e `substance_status: PENDING`
de forma honesta: corrigir a forma não inventa aprovação nem prova de voz.

## Estado final

| Item | Situação |
|---|---|
| Código alterado localmente | ✅ 116 testes aprovados |
| Commit / push | ❌ Não feitos |
| WordPress alterado | ❌ Nenhum post modificado |
| Publicação | ❌ Nenhuma |
| Alterações preexistentes do usuário | ✅ Preservadas (`image_protocol.py`, catálogo, documentos) |
