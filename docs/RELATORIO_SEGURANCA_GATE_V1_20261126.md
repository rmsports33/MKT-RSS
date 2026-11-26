# RELATÓRIO DE SEGURANÇA — GATE V1 (26/11/2026)

**Branch:** `feat/gate-v1-novo-painel-20261126`  
**Status:** ✅ SEGURO (implementação isolada, sem produção)

---

## 1. Controles de segurança implementados

| Controle | Implementação | Evidência |
|----------|---------------|-----------|
| Identificação do artigo | `post_id` obrigatório e validado | Teste 10 |
| Hash da versão analisada | `snapshot_hash` comparado com `cxgv1_hash_snapshot()` | Teste 12 |
| Proteção contra versão diferente | Bloqueia se hash divergente | Teste 12 |
| Duplicidade de decisão | `cxgv1_decision_exists()` + idempotência de fila | Teste 11 |
| Permissões WordPress | `cxgv1_is_owner_reviewer()` verifica `manage_options` + ID | Teste 14 |
| Proteção CSRF | `wp_localize_script` com nonce REST (`cxgv1_nonce`) | Template + Teste 14 |
| Preservação de histórico | `cxeg_review_` não sobrescrito sem nova versão | Teste 13 |
| Registro de erros de encaminhamento | Erro retornado com decisão preservada | Teste 10 |
| Não perder decisão se encaminhamento falha | `update_option()` antes do encaminhamento | Código |
| Não publicar automaticamente | Destino `publish_queue`, não `publish` | Teste 15 |
| Não sobrescrever evidências | Novas chaves `cxgv1_*_queue_{id}` separadas | Código |
| Aprovação não substitui qualidade | `cxeg_quality_valid()` exigido | Teste 4, 7 |

---

## 2. Permissões

| Ação | Quem pode |
|------|-----------|
| Acessar painel | Somente `CXEG_OWNER_REVIEWER_ID` com `manage_options` |
| Listar rascunhos | Somente proprietário |
| Ver detalhes | Somente proprietário com `edit_post` |
| Salvar decisão | Somente proprietário |
| Encaminhar para fila | Automático após decisão válida |

---

## 3. Motivos de reprovação (confrontados com diretrizes)

Os 14 motivos foram derivados das diretrizes efetivamente existentes no projeto:

| Motivo | Origem da diretriz |
|--------|--------------------|
| Fontes insuficientes | `PAUTAS_SELECIONADAS_20261117.md`, `EDITORIAL_ORCHESTRATION_GATE_20261110.md` |
| Afirmações sem comprovação | `EDITORIAL_DNA_V1`, `docs/REGENERACAO_MOTOR_20261117.md` |
| Divergências não explicadas | `PAUTAS_SELECIONADAS_20261117.md` (divergência Senado) |
| Dados numéricos sem fonte | `M04.17E_PRECO_EVIDENCIA.md` |
| Contexto brasileiro ausente | `AGENTS.md` (ConexoTech) |
| Análise superficial | `EDITORIAL_SUBSTANCE_20261110.md` |
| Texto incompleto/repetitivo | `linguagem_validator.py`, `html_paragrafos.py` |
| Identidade editorial ausente | `EDITORIAL_ORCHESTRATION_GATE_20261110.md` |
| SEO inadequado | `cxeg_reviewed_seo_valid()` |
| Imagem ausente/inadequada | `cxgna_media_readiness()` |
| Referências insuficientes | `EDITORIAL_DNA_V1` |
| Briefing/persona ausente | `EDITORIAL_SUBSTANCE_20261110.md` |
| Rastreabilidade incompleta | `conexo-mkt-trace.php` |
| Alteração após aprovação | `cxeg_review_*` + hash |

**Nota:** Nenhuma regra foi inventada. Todas derivam de documentos/código existentes.

---

## 4. Testes de segurança

| Teste | Resultado |
|-------|-----------|
| Permissões e CSRF | ✅ PASS |
| Duplicidade de requisição | ✅ PASS |
| Integridade do hash | ✅ PASS |
| Reprovação sem justificativa bloqueia | ✅ PASS |
| Ausência de publicação automática | ✅ PASS |

---

**Conclusão:** O novo painel implementa todos os controles de segurança exigidos, sem enfraquecer o Gate V1.
