# ConexoTech — gate editorial: situação verificável em 04/11/2026

**Status:** INTEGRADO_EM_BRANCH / BLOQUEIO_REMOTO_INATIVO / NAO_HOMOLOGADO.
Nenhum passo abaixo autoriza ativação automática, merge, publicação ou
GitHub Actions. Operação supervisionada pelo WordPress MCP permanece possível
com revisão factual e aprovação específica do artigo.

## Evidência do WordPress real (somente leitura)

- WordPress MCP conectado ao site `conexotech.com.br`, acesso disponível.
- `Conexo Editorial Gate`: **inactive**, identificado como
  `mu-plugins/conexo-editorial-gate`; **versão e hash no servidor não medidos**.
- `Conexo Native SEO (Staged)` 0.5.1: active.
- Rank Math e UpdraftPlus: active. Isso não comprova backup restaurável.
- GET anônimo em `/wp-json/conexo/v1/editorial/seo-readiness` e
  `/wp-json/conexo/v1/editorial/snapshot/9717`: HTTP 404.
  Não confundir com homologação autenticada das rotas.
- Hostinger MCP não lista o site, mas **não faz parte** do caminho editorial.
- Publicador assinado em código, dependente do núcleo Conexo OS #42 e da
  implementação de servidor/site #52 e #58.
- PR de integração `MKT-RSS#39`: helper de publicação de artigos mantém
  `publish_package`; helpers legados de páginas, termos e Rank Math
  passam a recusar escrita fora do gate (commits `a2b87b9` e `c2468cd`).
  Quatro novos testes cobrem proibição de HTTP por helpers legados.
  Houve **6/6 verificações estáticas**; os testes Python dessas correções
  **não foram executados neste checkout**.

## Condições cumulativas para ativação do gate no site

1. Revisar impacto funcional em páginas institucionais, taxonomias, autosave,
   rascunhos, uploads/SEO e tarefas de cron; impedir perda de capacidades.
2. Medir SHA-256 da versão instalada no servidor e conferir contra a versão
   escolhida do PR #58 ou #52. Não confiar apenas no nome do plugin.
3. Confirmar backup completo com prova de restauração **em ambiente isolado**
   e rollback específico do MU-plugin. Ter forma de desabilitar/recuperar o
   plugin caso o wp-admin fique bloqueado.
4. Preparar executor confiável real e provisionar o mesmo segredo de assinatura
   no executor e WordPress, por armazenamento protegido, sem Git/chat/logs.
   Confirmar se o modo SEO estrito está desligado ou se o readiness SEO
   assinado foi homologado com chaves e contrato correspondente.
5. Testar em ambiente isolado, pela ordem: saúde do WordPress; criação de
   draft técnico autorizado; leitura de snapshot; rejeição de escrita direta
   sem recibo; edição supervisionada; publicação/agendamento com ordem e
   versão aprovadas; readback; nonce idempotente; expiração/replay; cron;
   imagens e metadados SEO; rollback.
6. Só depois habilitar o gate em produção com monitoramento e janela de
   recuperação; verificar imediatamente WP admin, API WordPress e posts
   anteriores. Na falha, suspender executor e reverter apenas a versão do gate
   usando o backup comprovado; não abrir fallback permanente.
7. Registrar evidências concretas do teste e do aceite; apenas então considerar
   merge controlado, evitando Actions/CI faturável.

## Regra de operação hoje

Usar ChatGPT Work/WordPress MCP para preparar e revisar artigos; manter os
pacotes na fila até aprovação humana da versão específica. **Sem ativar gate
novo, não existe garantia técnica global contra escrita editorial direta**;
essa condição deve ser explícita. Nunca confundir sinal de revisão ou status
`PASS` isolado com autorização de publicação.

## Distinção SFTP

O MCP SFTP OAuth está implantado e nega acesso anônimo (HTTP 401), mas
**não teve login OAuth válido nem leitura pelo novo MCP homologados**.
Seu uso para arquivos de tema é independente da publicação WordPress. Não
condicionar a operação editorial supervisionada à homologação SFTP.
