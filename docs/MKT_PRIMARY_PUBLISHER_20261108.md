# MKT-RSS como unico publicador

Pedido vigente: o MKT-RSS executa o ciclo editorial completo sem depender de uma conversa ChatGPT. A revisao/aprovacao humana por versao continua obrigatoria e pode ser registrada pelas rotas existentes do Gate WordPress. Conexo OS fornece o validador local fixado por hash, nao um servico publicador adicional.

Reutilizar `pipeline_rss.py --editorial-package` e `processar_pacote_editorial`, com `CONEXO_EDITORIAL_TRANSPORT=wp_broker`, uma identidade WordPress de editor nao-administrador e uma Application Password no ambiente operacional existente. A RC3 do Gate aceita somente `executor=mkt_rss`; nao exige uma conta WordPress-first. A configuracao de duas contas da RC2 requer migracao explicita no painel.

O pacote aprovado, `--core-root`, `--actor-id`, `--publication-reference` e `--trace-run-id` sao entradas do fluxo existente. O adaptador valida pacote e Turso antes de enviar ao broker. O wrapper `publicar_no_wordpress` agora tambem encaminha `trace_run_id`. Credenciais nunca entram no pacote. Modo SEO estrito continua bloqueado ate integracao do finalize assinado.

Uma retomada com nonce no modo broker e recusada antes da rede, pois esse modo ainda nao implementa consulta de operacao por nonce. Conferir estado remoto antes de nova tentativa; nao repetir POST automaticamente.

Esta entrega nao ativa cron de publicacao, nao muda producao e nao aprova materia. Homologacao de metadados Turso anterior nao equivale a E2E de publicacao. Proximo aceite: uma materia com qualidade, direitos de imagem e aprovacao de versao verificadas, executada pelo ambiente real MKT-RSS com readback.
