# P1 — Workflow de decisão supervisionada (preparado, não ativado)

Arquivo: `.github/workflows/rss-p1-supervised-synthetic.yml` na branch do PR #31.

## Limites de segurança

- Acionamento apenas `workflow_dispatch`, sem `push`, `schedule` ou `pull_request`.
- Job só prossegue no repositório `rmsports33/MKT-RSS`, branch `master`, ator `rmsports33` e ambiente `rss-homolog`.
- `P1_AUTHORIZED_ACTORS` é explicitamente não vazio; nenhuma identidade digitada pelo usuário é aceita na CLI.
- A escrita só cria uma **nova pauta sintética** sob `example.org/conexo-p1-supervisionada/<run_id>`, então seleciona esse mesmo ID. Não permite fornecer ID de pauta real.
- Falhas de autenticação, hostname e token bloqueiam a operação; WordPress, IA, agendadores e produção estão fora do escopo.
- `rss_editorial_triage.py --acao` permanece bloqueado fora deste fluxo.

## Antes de habilitar

1. Revisar PR #31, confirmar CI e aprovar **separadamente** integração de código.
2. Configurar, na UI GitHub do Environment `rss-homolog`, um revisor obrigatório elegível, caso o plano e as regras da conta permitam. O workflow **não cria nem garante** essa aprovação sozinho; se o recurso não estiver disponível, preservar acionamento manual restrito e não alegar dupla aprovação.
3. Verificar permissões do repositório, titularidade da conta e escopo do token Turso somente para homologação.
4. Validar um único run manual e a evidência de auditoria persistente. Não executar como consequência automática do merge.
5. Antes de aplicar decisões **reais**, implementar autenticação/autorização para pautas específicas, não apenas contexto do runner, e revisar o modelo de credenciais do banco.

## Risco residual

Variáveis do ambiente do runner e lista estática não constituem autorização criptograficamente isolada. Quem possui acesso para alterar workflow, environment ou secrets pode alterar a política. A proteção por triggers SQL pode ser removida com credenciais DDL. Essas limitações não estão resolvidas pela P1.
