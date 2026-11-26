# EVIDÊNCIAS DO PAINEL — GATE V1 (26/11/2026)

**Branch:** `feat/gate-v1-novo-painel-20261126`  
**Ambiente:** isolado (sem produção)

---

## 1. Estrutura do painel implementado

### Layout de duas colunas

**Coluna esquerda — Lista de artigos:**
- Miniatura (com placeholder "Sem imagem" quando ausente)
- Título clicável
- Data formatada (pt-BR)
- Categoria(s)
- Status editorial (draft/pending)
- Até 5 artigos iniciais (configurável via `cxgv1_list_drafts($limit)`)

**Coluna direita — Preview:**
- Imagem destacada
- Título
- Subtítulo (quando disponível)
- Conteúdo
- Categoria
- Data
- Status do Gate
- 3 abas: Pré-visualização, Detalhes, Verificação

### Decisão editorial

**APROVO:**
- Identifica revisor (`reviewer_id`)
- Registra data/hora (`reviewed_at`)
- Vincula à versão (`snapshot_sha256`, `version_sha256`)
- Prepara encaminhamento para fila de publicação
- Não publica automaticamente

**NÃO APROVO:**
- Lista de 14 motivos (seleção múltipla)
- Justificativa obrigatória
- Registra decisão e evidências
- Encaminha para correção no MKT-RSS

**SALVAR RESPOSTA:**
- Botão compacto e visível
- Validado antes de habilitar
- Persiste decisão via REST
- Não publica automaticamente

---

## 2. Evidências de código (arquivos)

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `mkt_flow_p0/gate_v1_painel_aprovacao.php` | Lógica de negócio (listar, decidir, encaminhar) | ~14 KB |
| `mkt_flow_p0/gate_v1_painel_aprovacao.js` | Interatividade (preview, abas, decisão, salvar) | ~11 KB |
| `mkt_flow_p0/gate_v1_painel_aprovacao.css` | Layout de duas colunas e estilos | ~9 KB |
| `mkt_flow_p0/gate_v1_painel_template.php` | Template + endpoints REST | ~8 KB |
| `tests/test_gate_v1_painel_aprovacao.php` | 15 testes (46 asserções) | ~20 KB |

---

## 3. Capturas do painel

**NOTA IMPORTANTE:** Conforme as regras de execução isolada, não foi possível gerar capturas reais do painel em WordPress, pois isso exigiria:
- Ativar o código no WordPress real (não autorizado)
- Escrever no WordPress (não autorizado)

As capturas reais ficam **PENDENTES** até que o código seja implantado em ambiente de testes homologado (fora de produção).

**Evidência textual disponível:**
- Estrutura HTML do template (`gate_v1_painel_template.php`)
- Estilos CSS aplicáveis (`gate_v1_painel_aprovacao.css`)
- Comportamento validado por 46 asserções

---

## 4. Resultados dos testes

```
php tests/test_gate_v1_painel_aprovacao.php

RESULTADO FINAL
PASS: 46
FAIL: 0
PENDENTE: 0
TOTAL: 46
```

---

## 5. Status das capturas

| Item | Status |
|------|--------|
| Captura do painel em ambiente de testes | ⏸️ PENDENTE (requer ambiente homologado) |
| Evidência textual do layout | ✅ DISPONÍVEL |
| Evidência de testes automatizados | ✅ DISPONÍVEL |
