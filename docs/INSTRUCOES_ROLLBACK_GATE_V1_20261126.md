# INSTRUÇÕES DE ROLLBACK — GATE V1 (26/11/2026)

**Branch:** `feat/gate-v1-novo-painel-20261126`  
**Status:** Rollback preventivo (implementação ainda não implantada em produção)

---

## 1. Situação atual

O código do novo painel **ainda não foi implantado em produção**. Está apenas em branch isolada no GitHub. Portanto, não há nada para reverter em produção neste momento.

---

## 2. Se o código for implantado e precisar ser revertido

### Opção A — Reverter apenas o novo painel (recomendado)

O novo painel é **aditivo**. Para desativá-lo:

1. Remover ou comentar as seguintes linhas do bootstrap do plugin:
   - `require_once .../gate_v1_painel_aprovacao.php`
   - `require_once .../gate_v1_painel_template.php`

2. O Gate V1 continua funcionando normalmente com:
   - `conexo-editorial-gate-core.php`
   - `conexo-owner-review.php`
   - `conexo-review-publisher.php`
   - Demais módulos existentes

3. Nenhuma decisão ou aprovação existente é afetada.

### Opção B — Reverter a branch inteira

```bash
git checkout master
git branch -D feat/gate-v1-novo-painel-20261126
git push origin --delete feat/gate-v1-novo-painel-20261126
```

**Atenção:** Isso remove apenas a branch. Não afeta o plugin instalado no WordPress.

---

## 3. Preservação de dados

| Dado | Local | Afetado pelo rollback? |
|------|-------|------------------------|
| Aprovações existentes | `cxeg_review_{id}` | ❌ Não |
| Pareceres de qualidade | `cxeg_quality_{id}` | ❌ Não |
| Histórico operacional | `cxsc_audit_{id}` | ❌ Não |
| Fila de publicação (nova) | `cxgv1_publish_queue_{id}` | ❌ Não (permanece para inspeção) |
| Fila de correção (nova) | `cxgv1_correction_queue_{id}` | ❌ Não (permanece para inspeção) |

---

## 4. Verificação pós-rollback

Após reverter, confirmar:

```bash
# Testes do Gate V1 devem continuar passando
python -m pytest tests/test_editorial_prova_voz.py tests/test_editorial_import_provenance.py -q
```

E no WordPress:
- `GET /wp-json/conexo/v1/editorial/quality/{id}` → HTTP 401 anônimo
- Página "Revisão do proprietário" continua disponível

---

## 5. Contato

Se houver dúvida sobre o rollback, **não executar**. Preservar o estado atual e solicitar avaliação.
