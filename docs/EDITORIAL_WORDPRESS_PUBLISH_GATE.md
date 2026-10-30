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
