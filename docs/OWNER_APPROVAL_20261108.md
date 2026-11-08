# Publicacao MKT-RSS com aceite do proprietario

O usuario autorizou expressamente aprovacao pelo proprietario em 08/11/2026, sem trocar autor nem criar terceiro usuario. O humano ID3 aprova, o servico ID4 publica. review_mode=owner nao alega revisao por outra pessoa. A politica antiga de independencia permanece no modo independent.

## Uso pelo celular/navegador

1. WordPress > Ferramentas > Revisao do proprietario, post_id=9768. Conferir o texto nas previas autenticadas de390/1440, a foto ilustrativa e suas referencias, as fontes e o SEO. Somente marcar itens efetivamente conferidos; o formulario nao marca nem aprova nada automaticamente.
2. Aprovar a versao. A tela salva o parecer e o aceite pelo usuario autenticado e mostra version_sha256. Essa acao nao publica.
3. GitHub Actions > Publish owner-approved article - MKT-RSS > Run workflow > master. Informar post_id, copiar a versao exibida e confirmar PUBLICAR. O ambiente protegido rss-homolog continua sujeito as mesmas regras.
4. Resultado deve confirmar verified=true, publicacao_seo_concluidos=true e seo_public_verified=true. O ultimo campo verifica por GET publico, sem senha, que ha um unico titulo, descricao e canonical iguais aos aprovados. Se falhar, o resultado informa que a publicacao ja ocorreu e exige inspecao, sem repetir POST. Nao repetir job por reflexo.

O fluxo usa pacote privado conexo-owner-release/1 servido pelo proprio Gate RC5. Nao precisa do servico Conexo OS nem de sessao ChatGPT. O caminho legado editorial-workflow/2 continua usando o validador original; nao ha fallback automatico entre modelos.

O cliente autentica ID4, le somente a versao exata aprovada e registra trilha de metadados Turso com leitura de confirmacao. O evento generation registra importacao do draft existente, sem afirmar que um LLM gerou texto nesta execucao. As etapas de revisao PASS se referem aos checks que o proprietario realmente confirmou no WordPress; nao derivam de ausencia de alertas.

O mesmo broker revalida pacote privado, snapshot, aprovacao, SEO e permissao; assina dentro do WordPress, publica uma vez e finaliza SEO. A reserva por versao impede repeticao automatica. A aprovacao expira funcionalmente quando o snapshot muda; o post publicado nao volta como liberavel.

89 testes Python relacionados passaram. Contraparte WordPress passou66 verificacoes descartaveis, incluindo owner=autor, servico impedido de aprovar, ausencia de aceite/evidencia, previas, autoria preservada, pacote privado, publicacao+SEO, reserva, versao alterada e slug duplicada. Nao sao publicacoes reais.

Limite operacional: conector GitHub nao oferece workflow_dispatch e ferramentas desta sessao nao controlam o navegador WordPress autenticado do usuario. O aceite humano e o disparo manual precisam ocorrer nas interfaces acima; nao fabricar registros para compensar isso. Nenhuma materia foi publicada na preparacao.
