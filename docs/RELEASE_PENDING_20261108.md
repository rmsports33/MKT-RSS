# Checkpoint — concluir pendencias MKT-RSS

## Confirmado nesta etapa

- WordPress: Gate RC3 ativo, Vault ativo, Rank Math ativo; credencial MKT-RSS editor ID4 homologada na execucao Actions 42513958227 anterior. Tela do usuario confirmou allowlist ID4.
- Contraprova real RC3: post sintetico #9791 criado draft; tentativa de agendamento em 2099 sem aprovacao recusada com conexo_editorial_blocked/403; readback draft, nunca publicado.
- Encontrado defeito de lixeira: RC3 retornou rest_cannot_delete/500 porque o guard rejeitava a transicao nativa draft->trash. Corrigido no site em RC3.1, apos 40 verificacoes WordPress/MariaDB descartaveis, 53 verificacoes PHP e 17 contraprovas broker. Loader e finalize SEO tambem passaram.
- RC3.1 confirmada ACTIVE por leitura independente. Vault continuou ativo, Hostinger is_valid=true. Limpeza #9791 confirmada status=trash por duas ferramentas. O upload retornou erro de slug apos substituir os arquivos; nenhuma repeticao de upload foi feita, pois a leitura confirmou a versao aplicada.
- Preparado workflow manual `mkt-release-readiness-manual.yml`: identidade, allowlist via contrato invalido post_id=0, snapshot #9768, GET de prontidao SEO e leitura da prova sintetica Turso ja existente. Nao publica, nao agenda, nao cria parecer/aprovacao ou trilha PASS. 42 testes Python locais passaram (6 do novo probe, 11 de identidade e regressoes broker/trace/SEO).

## Pendente com criterio de conclusao

1. **Executor real:** iniciar uma execucao manual do workflow `MKT release readiness - no article writes`, branch master, ambiente rss-homolog protegido. O conector GitHub nao oferece dispatch e o Cloud nao possui os secrets; nao alterar protecoes ou gatilhos para contornar essa limitacao. Ver resumo sanitizado com identidade/broker/snapshot/Turso PASS. Um job verde nao significa publicacao autorizada ou SEO estrito pronto.
2. **SEO estrito:** verificar flags seo_signing_ready e seo_public_output_ready. O adaptador broker ainda recusa CONEXO_REQUIRE_SIGNED_SEO=1; nao desligar a exigencia para obter PASS nem confundir Rank Math ativo com finalize assinado homologado. Integracao da finalizacao e configuracao privada de chave permanecem pendentes e nao foram declaradas concluidas.
3. **Materia real:** pacote canonico, fatos/fontes, direitos de imagem, apresentacao, trilha Turso da versao e parecer/aprovacao humana independentes. Artigo #9768 continua draft, autor ID3 e imagem9714; nao houve alteracao de conteudo. O proprio autor3 nao pode aprova-lo. Nao trocar autoria somente para contornar o Gate, nem inventar revisor. Autorizacao geral de engenharia nao aprova essa materia.
4. **Publicacao E2E:** executar uma unica operacao MKT-RSS de versao efetivamente aprovada e conferir snapshot/status/SEO. Sem nova tentativa automatica em resposta incerta. Nenhum artigo real foi publicado nesta etapa.

## Proximo passo pelo celular

Abrir Actions > MKT release readiness - no article writes > Run workflow > master > Run workflow; aprovar o ambiente caso solicitado. Enviar somente o link da execucao, nunca secrets. O probe envia uma unica requisicao POST deliberadamente invalida ao broker, comprovada no codigo RC3.1 como rejeitada antes de snapshot/assinatura/reserva/escrita, e usa consultas para os demais itens.

Recomendacao: usar esse unico relatorio para decidir a proxima correcao concreta; nao repetir homologacao de identidade, criar novas contas ou expandir o executor sem necessidade demonstrada.
