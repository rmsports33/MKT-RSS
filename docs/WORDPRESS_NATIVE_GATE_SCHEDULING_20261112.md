# Publicação ConexoTech com Gate Único e WordPress nativo — 12/11/2026

## Decisão arquitetural

**Um único Gate:** o plugin já ativo **Conexo Editorial Gate 0.1.0-rc5** no WordPress. O MKT-RSS continua sendo o único executor editorial remoto. Não criar conta/revisor/broker paralelo. A autoria técnica dos seis rascunhos é WordPress ID 4 (Bot.editor); o revisor proprietário autenticado é o administrador WordPress ID 3.

**Agendamento preferido:** o núcleo WordPress e o WP-Cron, com recibo versionado emitido pelo mesmo Gate. O código existente do Gate já aceita `schedule`, guarda `cxeg_schedule_<id>` contendo hash de snapshot e UTC e, ao disparar `publish_future_post`, confere novamente hash e horário. Não agendar diretamente por `wp/v2/posts` porque o Gate bloqueia alterações de status fora da via assinada.

**Economia do Actions:** a rotina de seis jobs de 12/11 foi removida em favor de uma **única execução manual** para instalar os seis agendamentos depois das assinaturas humanas, sem cron periódico do GitHub. Workflow: [Agendamento WordPress nativo](https://github.com/rmsports33/MKT-RSS/actions/workflows/schedule-wordpress-approved-batch-manual.yml).

## Aceite real do proprietário — não automatizar assinatura humana

O formulário atual do Gate pré-preenche sugestões de evidência, apresenta fontes, capa, preview 390/1440, título/descrição/canonical SEO e 13 verificações. São **preparações automáticas, não comprovação de que foram verificadas**. Somente o WordPress autenticado como proprietário ID 3 pode atestar as verificações, marcar os controles e enviar a aprovação da versão atual. O aceite do usuário no ChatGPT é a deliberação editorial, mas **não cria o recibo autenticado do Gate**. Se qualquer post mudar depois do aceite, a aprovação anterior fica inválida.

Fila de revisão para o mesmo proprietário, sem outra conta:

| Post | Link de revisão |
|---|---|
| 9813 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9813 |
| 9815 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9815 |
| 9814 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9814 |
| 9810 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9810 |
| 9816 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9816 |
| 9817 | https://conexotech.com.br/wp-admin/tools.php?page=conexo-owner-review&post_id=9817 |

**Pré-requisito operacional a confirmar:** a opção interna `cxeg_broker_authorized_actors` precisa designar `mkt_rss=4`; o código do Gate exige isso para validar o revisor proprietário, além de `CXEG_OWNER_REVIEWER_ID=3`. Não presumir que a configuração existe só porque o plugin está ativo. O painel existente **Ferramentas → Conexo Gate: executores** fornece a seleção da conta de serviço; somente o proprietário deve confirmá-la.

## Agendar os seis depois dos seis recibos Gate

Escolher uma data realmente futura, **pelo menos 10 minutos adiante do momento da execução**. Para o lote atual já interligado, usar uma janela curta excepcional de 50 minutos (as matérias se citam mutuamente), em vez de distribuí-las por três dias com links temporariamente quebrados.

Após as seis assinaturas, abrir o workflow manual acima na branch `master`, informar `start_local` em `YYYY-MM-DDTHH:MM` do fuso `America/Fortaleza` e `confirm=AGENDAR_SEIS`. Não executar se ainda não houver seis recibos autênticos. O script faz preflight **de todos antes da primeira escrita**; se faltar um, nenhum post é agendado. Verifica status de rascunho, autor 4, capa específica, corpo igual à versão aprovada, data UTC, trilha privada Turso e retorno real da via assinada. Se houver incerteza após alguma escrita, interrompe e exige reconciliação antes de qualquer repetição.

A sequência automática está codificada como: 9813, 9815, 9814, 9810, 9816, 9817, a cada dez minutos. O código não publica na execução de agendamento: WordPress guarda seis posts como `future` e o Gate protege o cron de publicação.

**Limitação SEO real:** o broker atual permite Conexo Native SEO assinado na publicação imediata, mas não finaliza o contrato nativo no modo `schedule`. O fluxo novo recusa alegar SEO finalizado; Rank Math continua ativo como solução atual, mas a saída pública deverá ser auditada após o primeiro disparo. Não declarar homologação SEO nativa para cron sem mecanismo e verificação adicionais.

## Executar WP-Cron sem GitHub

O **WP-Cron nativo é gratuito** e funciona quando o site recebe visitas, mas pode atrasar num site de baixo tráfego. Na Hostinger, o hPanel tem **Sites → Gerenciar → Avançado → Cron Jobs**. Na hospedagem Business compartilhada, a API Hostinger disponibilizada nesta sessão não oferece operação para criar cron da conta; a ação no hPanel não foi executada.

Caso o plano permita intervalos de 5 minutos, criar uma tarefa cron **sem comprar produto novo** com:
- Tipo: Custom.
- Expressão cron: `*/5 * * * *` (UTC no hPanel, irrelevante para periodicidade de cinco minutos).
- Comando sugerido pela Hostinger: `wget -q -O - "https://conexotech.com.br/wp-cron.php?doing_wp_cron" > /dev/null 2>&1`.

**Não** desligar WP-Cron do WordPress em `wp-config.php` antes de conferir que a tarefa de servidor realmente executa. Não alterar config sem backup. A função WP-Cron já pode trabalhar sem essa tarefa, apenas com risco de atrasos.

Referências: WordPress developer cron handbook https://developer.wordpress.org/plugins/cron/ ; Hostinger setup https://www.hostinger.com/support/1583465-how-to-set-up-a-cron-job-at-hostinger/ .

## Cadência saudável para futuros lotes

- **Rotina inicial: 1–2 artigos completos por dia**, com horários aproximados 09h e 17h BRT, espaçados e ajustados depois de 14–30 dias com Search Console, GA4 e cliques internos. Um terceiro artigo apenas para notícia urgente com apuração completa.
- **Não** adotar publicação de seis simultâneos por padrão: compete por atenção na home, pode gerar notificações em bloco e impede avaliar a audiência de cada artigo.
- **Lote atual é exceção:** seis matérias do mesmo núcleo editorial já estão cruzadamente interligadas, portanto janela curta de 50 min é preferível para não manter links para rascunhos indisponíveis por dias.
- Em pauta futura, inserir no texto links **somente para posts já publicados**; 'Leia também' deve ser relevância editorial, não preenchimento artificial.
- O Google não determina quantidade obrigatória de posts. Priorizar profundidade, utilidade e diferenciação factual.

## Status em 12/11/2026

- Gate 0.1.0-rc5, Conexo Native SEO 0.5.2, Rank Math ativos (conector WordPress).
- Seis conteúdos aprovados editorialmente pelo proprietário no ChatGPT, cada um com links internos, capa específica e autor ID4.
- Todas as seis leituras WordPress por ID retornaram `draft` antes deste registro; **nenhuma assinatura atual do Gate foi comprovada**.
- A integração para um agendamento WordPress único está em código e CI, **não foi executada contra WordPress real** porque falta confirmar os recibos autenticados do Gate e o cron da hospedagem.
- Evitar retrabalhos ou publicação direta fora do Gate.
