# Plano de Estrutura — MKT Flow / Redator / Suite (12/09/2026)

## Objetivo
Melhorar a estrutura do projeto **sem quebrar nada em uso** (nuvem ativa,
artigos publicados, suíte verde). Progressividade e segurança juntas.

## Princípios (travas por padrão)
1. **Suíte verde = linha de chegada de cada bloco.** Nada é "pronto" sem
   `python -m pytest tests -q` verde + `git push`.
2. **Bloco pequeno, nunca big-bang.** Cada mudança estrutural tem causa
   única e rola back se quebrar.
3. **2 testes novos por mudança estrutural.** A rede de segurança anda na
   frente do quebra-cabeça.
4. **Migração com cópia de segurança.** Já aprendemos isso do jeito caro
   (incidente 12/09) — nada de `Remove-Item` sem backup + git commit.
5. **Depreciação visível, não exclusão silenciosa.** O que sai de produção
   vira `_legado/` com README, nunca some de surpresa.

## Alvos
- Raiz limpa: 33 arquivos soltos → ~10 (só entrypoints + docs essenciais).
- Núcleo `mkt_flow_p0/` como única fonte de verdade de compliance/estrutura.
- `MKTFLOW/` clássico congelado e marcado; redator com fonte de specs própria.
- Testes organizados por camada (`tests/p0/`, `tests/legado/`, ...).

## Passos (em ordem, cada um com testes + commit)

### Bloco A — organização de teste (sem tocar em código de produção)
1. Criar `tests/unit/`, `tests/e2e/`, `tests/legado/` e mover testes.
   - `tests/legado/` recebe os que importam `MKTFLOW.*` (23 testes hoje).
   - Cria `conftest.py` raiz com sys.path estável.
2. Configurar `.github/workflows/ci.yml` para rodar a suíte nova.
3. Rodar suíte, conferir verde, commit.
   - Segurança: nenhum código de produção muda aqui.

### Bloco B — raiz limpa
4. Mover utilitários soltos (`diagnostico_drive.py`, `drive_command.py`,
   `backup_drive.py`, `google_drive_client.py`) para `scripts/` (com
   `sys.path` ajustado ou import relativo).
5. Mover landings antigas (`landing_*.html`) para `outputs/landings/`.
6. Consolidar `requirements-*.txt` num `requirements/` ou manter 1 + slim.
7. Testar, commit.

### Bloco C — MKTFLOW congelado
8. Criar `_legado/MKTFLOW/` e mover `MKTFLOW/` (menos `venv/`) com README
   de depreciação.
9. Atualizar `sys.path` dos 23 testes legados para apontar pro `_legado/`.
10. Conferir que nenhum import de produção toca `MKTFLOW/` novo.
11. Testar, commit.

### Bloco D — entrada única de dados (fonte primária)
12. Criar `scripts/atualizar_fichas.py` que busca ficha na internet
    (fonte primária) e atualiza `curated_specs.json` do redator.
13. Mover `data/` do redator para `redator-artigo-blogs/data/` (já é).
14. Testar, commit.

## Critério de sucesso
- Raiz: ≤10 arquivos soltos.
- Suíte verde após cada bloco.
- Nuvem intacta (nenhum endpoint/processo muda de nome).

## Fora do escopo (não fazer nesta rodada)
- Migrar TODOS os testes `MKTFLOW.*` para o núcleo (já começamos; o resto
  fica para rodada dedicada, pois toca persistência de DB diferente).
- Reescrever o redator inteiro — só adicionar fonte primária.