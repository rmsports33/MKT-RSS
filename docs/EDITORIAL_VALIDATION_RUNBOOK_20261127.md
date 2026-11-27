# Roteiro único de homologação — contrato editorial v1.1

**Objetivo:** executar e fechar as validações técnicas pendentes em ambiente descartável, sem WordPress ativo, sem publicação, sem deploy e sem novo custo de IA.

**Contrato canônico:** ConexoTech v1.1, SHA-256 `6b55c87c15b004169a77a73d3064fb02072c1cc370e7c9be68bee20e9abde9f7`.

**Política de execução:** o MKT-RSS não usa GitHub Actions como executor padrão de testes. Usar workspace isolado/Codex Cloud ou ambiente de desenvolvimento equivalente. Não usar secrets, .env, credenciais WP, credenciais Turso ou chave Groq. As suítes abaixo devem funcionar com mocks/fixtures.

---

## 0. Preparação e salvaguardas

- Fazer checkout exato das branches/SHA listadas em cada PR antes de testar.
- Guardar alterações preexistentes; não fazer reset destrutivo.
- Não instalar, ativar ou chamar plugin no site ativo.
- Não executar comandos de importação/publicação/cron nem scripts de integração contra conexotech.com.br.
- Não executar ASVE real contra artigo WordPress até concluir testes offline.
- Se algum teste tentar rede, WordPress, Turso ou LLM, interromper e substituir por mock/fixture; registrar o teste que tentou sair do ambiente isolado.

## 1. MKT-RSS — PR #142

Repo: `rmsports33/MKT-RSS`  
Branch: `feat/editorial-quality-score-20261127`

Preparação no checkout, usando o ambiente virtual já presente:
```bash
python -m pip install -r requirements/base.txt
```

Primeiro, suíte focada das funcionalidades alteradas:
```bash
python -m pytest -q \
  tests/test_editorial_secondary_analysis.py \
  tests/test_primary_source_registry.py \
  tests/test_editorial_secondary_reviewer_integration.py \
  tests/test_wp_quality_executor.py \
  tests/test_fila_pautas.py \
  tests/test_editorial_gate_traceability.py \
  tests/test_editorial_quality_score.py \
  tests/test_editorial_golden_set.py \
  tests/test_revisor_qualidade_unico.py
```

Depois, regressão das fronteiras relacionadas:
```bash
python -m pytest -q \
  tests/test_editorial_substance.py \
  tests/test_provider_budget.py \
  tests/test_editorial_import_public.py \
  tests/test_editorial_draft_complete_readback.py \
  tests/test_related_links_contextual.py
```

Se ambas passarem, executar a suíte do repositório:
```bash
python -m pytest tests -q
```

Critérios:
- Zero falhas; registrar contagem exata de passed/skipped/failed.
- Nenhuma chamada real de LLM, WordPress ou Turso.
- Testes de ASVE comprovam versão/hash exato, contexto independente, zero a cinco achados, P0/P1/P2, rejeição de reescrita, validação de links publicados e persistência P2 somente sob flag explícita.
- Score não cria quota para links internos, não aplica mapa Canaltech a gêneros incompatíveis, não aprova factualidade por domínio/TLD e mantém os sinais brasileiros como consultivos.
- Registrar SHA do checkout e comando integral executado no recibo de validação.

## 2. Bot-redator-artigo — PR #6

Repo: `rmsports33/bot-redator-artigo`  
Branch: `docs/editorial-quality-contract-20261126`

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests/test_editorial_prompt_contract.py tests/test_fundational_identity.py
```

Se passar, executar:
```bash
python -m pytest tests -q
```

Critérios:
- Prompt preserva todas as guardas já existentes de preço, specs, alegações de testes e fontes por categoria.
- Novo contrato inclui pesquisa global apenas quando pertinente, diferenças regionais materiais, Brasil sustentado, estrutura narrativa, fontes por claim e links internos sem quota.
- Nenhuma chamada de geração de artigo/LLM é necessária para validar o prompt.

## 3. Gate V2 — PR #87

Repo: `rmsports33/-site-conexotech`  
Branch: `feat/conexo-editorial-gate-v2-foundation-20261123`

A suíte PHPUnit e PHP lint apresentaram checks verdes na execução consultada. Não repetir sem necessidade, salvo se o SHA mudar ou o teste de integração exigir.

Para reprodução isolada no checkout:
```bash
cd plugins/conexo-editorial-gate-v2
composer install --no-interaction --prefer-dist
composer test
```

Para a integração WordPress, reproduzir **somente** os passos do job `wordpress-integration` em `.circleci/config.yml`, com WordPress e MariaDB descartáveis (localhost/container efêmero). O smoke test é:
```bash
php wp-cli.phar eval-file plugins/conexo-editorial-gate-v2/tests/integration/wordpress-smoke.php --path="$HOME/wordpress" --allow-root
```

Não usar URL, senha, banco ou usuário do site ativo. Localizar a primeira etapa que falha, capturar a mensagem/stack trace, corrigir a causa mínima e repetir apenas o job afetado, além de PHPUnit se código PHP mudar.

Critérios:
- PHP lint e PHPUnit verdes no mesmo SHA da alteração de política /2.
- Smoke test WordPress passa no WordPress descartável.
- Teste com 12 links internos permanece `REVIEW_REQUIRED`, sem bloqueio de contagem.
- Política /2 e hash correspondente estão presentes no catálogo e nos Quality Records; recibo calculado sob política antiga não é reutilizado.

## 4. Fechamento de integração

Só depois das suítes verdes:

1. Comparar novamente contrato e catálogo canônicos/operacionais.
2. Revisar conflitos de arquivos entre PRs; PR #141 permanece documental e limitado à nota do Gate V1.
3. Atualizar os PRs com SHA, comandos, contagens e links para logs/recibos.
4. Manter os PRs como draft enquanto a homologação editorial não estiver concluída.
5. Executar piloto ASVE offline com três gêneros diferentes, utilizando fixtures já aprovadas. Comparar resultados com avaliador humano; medir utilidade e falsos positivos.
6. Somente então solicitar decisão editorial humana para o artigo #9925. A minuta de esclarecimento à EPE permanece preparada, mas não enviada.

## Critério final de conclusão

Não declarar concluído com base apenas em código presente ou PR existente. Exigir: testes executados e verdes nos SHAs identificados; integração WordPress efêmera aprovada; contrato/catálogo consistentes; piloto editorial com avaliação humana; e recibos de rastreabilidade verificáveis.

**Nenhuma destas validações autoriza merge, deploy, ativação do plugin, escrita no WordPress ou publicação de artigo.**
