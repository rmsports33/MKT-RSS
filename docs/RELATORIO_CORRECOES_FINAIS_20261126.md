# RELATÓRIO DE CORREÇÕES FINAIS — PR #135 e #136 (26/11/2026)

## Classificação adotada
- **PASS**: teste automatizado reproduzido localmente.
- **PASS SIMULADO**: comportamento validado apenas com mocks/sessão simulada.
- **PENDENTE**: depende de ambiente WordPress real (homologado).
- **PENDENTE DE AUTORIZAÇÃO**: depende de operação real (publicação/escrita).

---

## PR #135 — Gate V1 (correções)

| # | Correção | Classificação | Evidência |
|---|----------|---------------|-----------|
| 1 | Conectar layout à tela nativa `cxeg_owner_page()` | ✅ PASS | hook `admin_notices` em `page=conexo-owner-review` |
| 2 | Listagem e preview via rotas/funções nativas | ✅ PASS | `cxgna_eligible_drafts` + `/snapshot/{id}` |
| 3 | SALVAR RESPOSTA executa salvamento nativo | ✅ PASS | `form.requestSubmit()` no formulário nativo |
| 4 | Formulário nativo por ID único | ✅ PASS | `cxgv1nat-native-form` (sem `querySelector('form')`) |
| 5 | Não marcar 13 critérios / não inventar evidências | ✅ PASS | JS não marca; PHP exige checks reais |
| 6 | Destino nativo preservado | ✅ PASS | JS não altera `publication_mode` |
| 7 | Reprovação no histórico nativo | ✅ PASS | `cxeg_review_{id}` com `decision=rejected` + nonce nativo |
| — | Testes | ✅ PASS | 16 Python + 14 PHP |

## PR #136 — MKT-RSS (complementos)

| # | Correção | Classificação | Evidência |
|---|----------|---------------|-----------|
| 1 | Adaptador real do registro confiável | ✅ PASS SIMULADO | `registry_adapter_real.py` + 2 testes mock |
| 2 | Chaves separadas (sem expor valores) | ✅ PASS | `review_keys.keys_status()` + 2 testes |
| 3 | Destino WordPress (PR #133) | ✅ PASS SIMULADO | `wp_destination` reforçado no broker |
| 4 | E1 e E2 no servidor | ✅ PASS SIMULADO | `readback_e1e2.py` + 3 testes mock |
| 5 | Guarda antes de qualquer escrita | ✅ PASS | teste prova POST não ocorre se guarda falha |
| 6 | Readback e recibo verificáveis | ✅ PASS SIMULADO |Broker já valida readback + `retry_automatic=False` |
| — | Testes novos | ✅ PASS | 7 + 2 testes |
| — | Regressão V1 | ✅ PASS | 479 testes |

## Validação final do ciclo

| Etapa | Classificação |
|-------|---------------|
| Seleção da pauta | ✅ PASS SIMULADO |
| Geração do artigo | ✅ PASS SIMULADO |
| Validação factual e editorial | ✅ PASS |
| Certificação | ✅ PASS |
| Revisão humana | ✅ PASS SIMULADO |
| Aprovação | ✅ PASS SIMULADO |
| Publicação autorizada | ⏸️ PENDENTE DE AUTORIZAÇÃO |
| Readback do WordPress | ✅ PASS SIMULADO |
| Recibo verificável | ✅ PASS SIMULADO |

**Nenhuma publicação real foi declarada concluída.**

## Pendências

| Item | Classificação |
|------|---------------|
| Adaptador real com credenciais de produção | ⏸️ PENDENTE (ambiente) |
| E1/E2 no WordPress real | ⏸️ PENDENTE (ambiente homologado) |
| Provisão das chaves separadas em produção | ⏸️ PENDENTE DE AUTORIZAÇÃO |
| Publicação real + readback remoto | ⏸️ PENDENTE DE AUTORIZAÇÃO |
| Capturas do painel em homologado | ⏸️ PENDENTE |

## Restrições respeitadas
- ✅ Sem merge, deploy, upload ou escrita em produção
- ✅ Sem SSH em produção
- ✅ Sem publicar artigos reais
- ✅ Sem excluir plugins, criar outro Gate ou refatorar fora do escopo
