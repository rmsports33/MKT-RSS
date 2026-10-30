# Integração de prontidão WordPress — PR #33

O módulo `editorial_publish_gate.authorize_publish(post, factual_review)` combina
a verificação de prontidão WordPress e aprovação factual. O orquestrador
`pipeline_rss.autorizar_transicao_publicacao` expõe esse contrato para futuros
adaptadores de publicação.

## Contrato de integração

1. Obter autorização factual atual e comprovada, não inferida do estado da fila.
2. Salvar rascunho, imagem, categoria e slug pelo adaptador WordPress existente.
3. **Ler novamente** o post persistido do WordPress (inclusive `featured_media`).
4. Invocar `autorizar_transicao_publicacao(post_persistido, revisao_factual)`.
5. Somente se `autorizado=True`, permitir uma transição explicitamente autorizada
   para `publish`; caso contrário, não escrever e registrar os bloqueios.
6. Após a escrita, reler o post e confirmar o status; falha não é sucesso.

O gate não realiza rede nem escrita e não pode validar que uma URL de imagem
existe fisicamente; o adaptador deve verificar a mídia via API WordPress.
O estado `CONCLUIDA` da fila RSS não é aprovação editorial.

## Limitação atual (fail-closed)

O `processar_item` em `pipeline_rss.py` retorna
`gate_factual_pos_ia_nao_integrado` antes de qualquer gravação no WordPress.
**Não existe um caminho operacional de publicação habilitado nesta branch.**
O novo guard está conectado como ponto de entrada do orquestrador, mas
nenhuma transição remota o chama porque nenhuma transição remota está ativa.
A ativação depende da integração de certificação factual e do adaptador
WordPress, seguida de testes de integração. Não contornar esse bloqueio.

## Testes locais (sem Actions)

```bash
python -m pytest -q tests/test_editorial_wordpress_readiness.py tests/test_editorial_publish_gate.py
```

Testes foram adicionados, mas não executados neste ambiente. Não habilitar
GitHub Actions, não fazer merge, deploy nem publicação a partir deste PR
antes de validar a integração real e obter autorização específica.

## Segurança adicional — 2026-10-30

Até existir um contrato de certificação factual independente, com identidade do
aprovador, evidências rastreáveis e vínculo ao artigo/SHA revisado,
`authorize_publish` **sempre** retorna `autorizado=False`, inclusive quando
um dicionário de flags diz `APROVADO`. A validação de prontidão é necessária,
mas não suficiente. `plan_publish_transition` também não retorna uma
solicitação de escrita executável. Esta é uma suspensão deliberada, não
uma homologação de publicação.

WordPress REST GET→POST não garante atualização atômica sob concorrência.
Uma futura implementação deve resolver idempotência e exclusão mútua de forma
verificável e testar falhas por mocks antes de qualquer teste supervisionado.

Validações locais nesta sessão: foram reproduzidos casos isolados em cópias
manuais consultadas via conector GitHub (11 passaram), **não** a suíte oficial
sobre um checkout verificado por SHA. A suíte integral continua pendente.

## Inspeção offline supervisionada

O método `editorial_wordpress_adapter.inspect_wordpress_draft(fetch_post, post_id, factual_review)` recebe uma função de leitura injetada. O orquestrador expõe `inspecionar_rascunho_wordpress`. Esta etapa lê dados persistidos simulados, normaliza campos `title.raw/content.raw` e executa o gate factual existente. Não realiza HTTP por conta própria e **não publica**.

Cinco testes isolados da nova etapa passaram no executor Python da sessão em 2026-10-30. Os arquivos foram reconstruídos manualmente a partir das versões consultadas; **não** representam o checkout completo validado pelo commit.

Para homologar: executar a suíte completa no SHA da branch, testar com mocks o adaptador REST integral, integrar fonte autenticada de revisão factual vinculada à versão do artigo e resolver concorrência transacional na transição do WordPress. Manter publicação automática desabilitada até isso ser comprovado.

## Contratos de segurança adicionados — 2026-10-30

- `editorial_factual_certificate.verify_factual_certificate(post, certificate, key)` confirma a autenticidade de uma decisão assinada por HMAC-SHA256, identidade declarada do revisor, referências HTTPS, validade máxima de 24 horas e vínculo SHA-256 ao rascunho persistido. **Não confirma a veracidade da reportagem nem a identidade real do revisor por conta própria**. A chave deve permanecer exclusivamente no servidor de certificação autorizado, nunca no coletor RSS, repositório, frontend ou logs.
- `editorial_atomic_transition.supervised_atomic_publish` exige um backend injetado `commit_if_unchanged(post_id, draft_digest, operation_id, certificate)`. O backend **ainda não existe na integração WordPress** e deve implementar exclusão mútua/compare-and-swap e idempotência no próprio servidor, além de confirmação persistida. GET seguido de POST via REST **não** oferece essa garantia.
- Estes módulos foram testados offline em cópias verificadas por hash Git (13 testes de comportamento passaram). A suíte completa do checkout Git **não foi executada**. A integração ao `editorial_publish_gate` continua deliberadamente fechada; uma assinatura correta isoladamente não autoriza publicar.
- O próximo passo exige: emissor autenticado e auditado com revisão humana independente das fontes; endpoint WordPress com transação e política de idempotência; testes de concorrência reais em homologação; suíte integral no SHA exato. Não alterar o estado do gate até comprovar esses requisitos e obter autorização operacional específica.
