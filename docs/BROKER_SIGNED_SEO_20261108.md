# Broker com finalize SEO no WordPress

Continua o pedido do usuario de executar pendencias. Baseline real Actions 42516640030 confirmou identidade, allowlist, snapshot e leitura Turso, mas assinatura/saida SEO e suporte do broker estavam false.

O modo CONEXO_EDITORIAL_TRANSPORT=wp_broker agora aceita CONEXO_REQUIRE_SIGNED_SEO=1 sem chave HMAC no executor. Exige Gate RC4/adaptador0.5.2 prontos, metadados aprovados no pacote e a mesma revisao humana no WordPress. Antes de publicar, consulta readiness e envia o hash dos quatro campos SEO revisados; servidor recusa divergencia. Segredos e assinaturas permanecem no WordPress.

Depois da publicacao, cliente verifica snapshot completo e finalize confirmado. Falha de finalize retorna erro com post_id/nonce e retry_automatic=false; nao simula sucesso e nao republica. Retomada automatica do broker continua recusada.

PASSOU: 79 testes Python relacionados. Contraparte WordPress passou 54 verificacoes em banco descartavel, incluindo contrato HMAC e gravacao privada; isso nao equivale a artigo aprovado ou HTML de producao.

Workflow manual mkt-release-readiness-manual.yml agora tambem exige strict_seo_ready=true para concluir verde. Reexecutar uma vez pela master apos implantacao da contraparte; conector GitHub ainda nao oferece dispatch. Nao alterar gatilhos ou extrair secrets para contornar essa limitacao.

Producao editorial permanece pendente de revisao/aceite por versao, direitos de imagem e teste de saida publica. Nenhum artigo foi publicado por esta mudanca e nenhuma aprovacao foi criada.
