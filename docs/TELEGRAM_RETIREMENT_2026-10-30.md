# Retirada do Telegram — 30/10/2026

Ordem: retirar a integracao Telegram; preservar RSS, WordPress e afiliados.
Estas alteracoes estao em PR separado de producao. Nao houve merge ou deploy.

## Correcao e prevencao

Remover somente o bot deixava receitas de hospedagem, SDKs opcionais,
reinstaladores e alertas que poderiam voltar a usar o Telegram. A retirada
inclui esses caminhos e um teste offline que reprova reintroducao do SDK,
polling ou notificacao. Historico documental permanece marcado como retirado.

## Evidencia executada

- `python tests/test_telegram_retirement.py`: 4 testes passaram.
- Preservacao AST dos helpers publicos de afiliados comparada ao head original.
- Helper tests existentes sem fixtures executados separadamente com HTTP falso;
  isso nao equivale a executar a suite pytest completa.
- `admin/bot.py`, dependencias do bot e polling ja removidos no PR; removidas
  tambem a receita Fly/Docker e as camadas opcionais de handlers.

## Limites e proximo passo

Nenhuma credencial consultada, token revogado, mensagem enviada, webhook alterado,
workflow disparado manualmente ou novo custo criado. Commits usam `[skip ci]`.

Integracao dos PRs e aplicacao no site sao etapas distintas. Antes de integrar
o repositorio do site, considerar o risco de auto-deploy e espelho GitLab
registrado nos PRs #50/#51. Nao usar o bloqueio de faturamento como protecao.

O manifesto Fly historico cita `mkt-rss-bot`; isso nao prova servico existente.
O WordPress informa ConexoTech Afiliados 1.11.1 ativo; a versao nao identifica
os bytes instalados nem prova webhook Telegram desligado. Preservar esse
plugin ativo para nao interromper links e rastreamento de afiliados.

Falta verificar e retirar apenas o webhook/configuracao Telegram e eventual
processo hospedado, pelo acesso seguro ao provedor. A remocao em branches nao
deve ser reportada como desligamento efetivo em producao.

## Conferencia administrativa posterior — 30/10/2026

Login renovado e identidade Reinaldo Mendes confirmada no painel WordPress.
O menu Assistente Telegram ainda existe na instalacao. Sua opcao
"Responder mensagens" (`cxaf_tg_ativo`) foi observada desmarcada. Nenhuma
configuracao foi salva ou alterada: o estado desejado ja estava desativado.
Somente metadados de controles foram lidos, sem valores de token, segredo ou chat.

Isso comprova a opcao visual desativada, nao exclusao dos arquivos do servidor,
cancelamento do webhook no Telegram, ausencia de poller em outro host nem
revogacao do token. A remocao efetiva do componente instalado permanece separada.
