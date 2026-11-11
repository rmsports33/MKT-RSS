# Homologação editorial real — quatro gêneros, sem publicação

**Data da conferência:** 2026-11-10 (BRT). **Ambiente:** WordPress ConexoTech de produção, exclusivamente rascunhos existentes e operações editoriais autorizadas. **Resultado:** preparação documental e correção de defeitos concretos concluídas; aceite humano independente e publicação **não** autorizados.

## Escopo e preservação

O piloto usa **artigos completos já existentes**, não exemplos reduzidos nem um novo executor. Há quatro gêneros: guia (#9798), notícia (#9635), análise (#9687), comparativo (#9681). A avaliação cega está preparada em um **Google Doc privado** que contém cinco textos completos: duas versões do guia, mais os outros três. A chave de correspondência está em outro documento privado, separado; nenhum manuscrito de rascunho foi inserido neste repositório público. O avaliador externo **ainda não respondeu**.

As edições abaixo foram feitas com `status=draft` e verificadas com leitura posterior do WordPress. As revisões antigas continuam disponíveis para rollback. Nenhum post foi publicado, nenhum fluxo de staging foi reativado e não houve chamadas adicionais ao Groq.

## Evidências dos artigos

| Gênero | Post | Revisão atual / ação | Fontes | Imagem | Estado |
|---|---|---|---|---|---|
| Guia | #9798 | #9806 (2026-11-10 18:22 BRT), +corroboração externa contextualizada, 100% do texto preservado | Apple (fontes primárias) + MacRumors (histórico independente do controle iOS 17.2) | mídia #9799 permanece, proveniência ChatGPT documentada; atestado definitivo de direitos e visual 390/1440 pendente | DRAFT, APTO A PARECER EXTERNO, NÃO PUBLICÁVEL |
| Notícia | #9635 | #9805 (18:18 BRT): corrigida inferência de 216 W e fabricante sem confirmação, contextualizada aprovação Anatel vs. assinatura | Tecnoblog + Exame + espelho do registro #01944-26-18192; confirmação direta no Certifica Anatel ainda necessária | mídia sem licença #9634 DESASSOCIADA, sem apagar arquivo | DRAFT, ATUALIZAÇÃO/CONFERÊNCIA NECESSÁRIA |
| Análise | #9687 | #9804 (18:17 BRT): retirada atribuição indevida a autores do veículo-fonte, substituído percentual sem respaldo e refinadas limitações | GDC, Quantic Foundry e NVIDIA como fontes primárias distintas | mídia sem licença #9686 DESASSOCIADA, sem apagar arquivo | DRAFT, ORIGINALIDADE/CONCLUSÕES PRECISAM DE AVALIADOR EXTERNO |
| Comparativo | #9681 | sem alterações na revisão editorial atual; texto integral em caderno privado | Samsung oficial para especificações; faltam observações/testes independentes para alegações de uso prolongado | featured_media=0; procurar imagem original/licenciada congruente | DRAFT, PENDENTE |

## Achados factuais e correções

**Guia #9798.** O suporte Apple confirma a diferença entre correção automática e texto preditivo, a separação das previsões em linha e a dependência de idioma. Português (Brasil) aparece em texto preditivo, mas não na lista específica de previsões em linha do catálogo Apple consultado. O MacRumors documenta que o controle independente foi introduzido no iOS 17.2; ele é **histórico**, não prova sozinho o comportamento de iOS 27.
- Apple: https://support.apple.com/pt-br/104995
- Apple: https://support.apple.com/pt-br/guide/iphone/-iphd4ea90231/ios
- Apple: https://www.apple.com/br/ios/feature-availability/
- MacRumors: https://www.macrumors.com/how-to/disable-iphone-inline-predictive-text/

**Notícia #9635.** Homologação de terminal não é anúncio de preço, cobertura nem contrato disponível. O modelo STG-S001-A0 e a data de 19/10/2026 são apoiados pelo espelho público de certificação e pela cobertura independente. A multiplicação 48 V x 4,5 A indica capacidade nominal de alimentação; não mede consumo contínuo. Havia divergência na identidade do fabricante entre fontes secundárias, e a redação agora exige verificação do processo regulatório antes de afirmá-la.
- Espelho certificado: https://fccid.io/ANATEL/01944-26-18192
- Exame: https://exame.com/tecnologia/starlink-chinesa-avanca-no-brasil-com-internet-via-satelite-veja-o-que-falta-para-chegar/
- Tecnoblog: https://tecnoblog.net/noticias/rival-chinesa-da-starlink-homologa-equipamento-no-brasil/
- Anatel — procedimento de homologação: https://www.gov.br/anatel/pt-br/assuntos/noticias/procedimentos-de-certificacao-e-homologacao-passam-a-ser-realizados-no-sistema-certifica

**Análise #9687.** A pesquisa opt-in da Quantic Foundry (N=1.799) não autoriza generalização a todos os gamers. O texto original afirmava 27% de rejeição a ajustes dinâmicos de dificuldade sem sustentação pelo relatório consultado; a fonte registra **26% positivos e 24% neutros**, o que não prova ampla aceitação. O levantamento GDC 2026 relata 52% de opiniões negativas entre profissionais da indústria. A NVIDIA apresentou DLSS 5 em março de 2026; o relato foi contextualizado. Foi removida uma biografia de autores do veículo-fonte indevidamente incorporada no rascunho do ConexoTech.
- Quantic Foundry: https://quanticfoundry.com/2025/12/18/gen-ai/
- GDC: https://gdconf.com/article/gdc-2026-state-of-the-game-industry-reveals-impact-of-layoffs-generative-ai-and-more/
- NVIDIA: https://www.nvidia.com/pt-br/geforce/news/dlss5-breakthrough-in-visual-fidelity-for-games/
- Fonte de partida devidamente atribuída no rascunho: https://olhardigital.com.br/2026/10/24/games-e-consoles/a-rejeicao-do-uso-de-ia-em-jogos-contra-seu-uso-no-desenvolvimento-de-hardware/

**Comparativo #9681.** IP54/67, seis atualizações e chipset foram conferidos em material Samsung, com as limitações usuais de região/modelo. O enquadramento editorial é semelhante ao da matéria independente publicada em outubro; revisão humana deve avaliar originalidade substantiva, não apenas divergência de redação.
- Samsung A16: https://news.samsung.com/br/samsung-apresenta-galaxy-a16-e-a16-5g-no-brasil-com-ate-seis-atualizacoes-de-sistema-android-e-seguranca
- Samsung A36: https://news.samsung.com/br/o-seu-primeiro-smartphone-galaxy-com-ai-samsung-apresenta-galaxy-a56-a36-e-a26-com-evolucao-da-inteligencia-artificial
- Reportagem para comparação de escopo (não copiar): https://canaltech.com.br/smartphone/galaxy-a36-vs-a16-5g-qual-celular-barato-da-samsung-vai-durar-mais/

## Critérios de aceite NÃO cumpridos

1. **Parecer externo humano e independente** para todos os textos e comparação cega A/B do guia. O caderno está completo e privado; não há notas ou assinatura independente.
2. **Direitos de imagem:** #9635 e #9687 já não têm mídia associada; #9681 está sem capa; #9798 tem origem declarada como saída ChatGPT, mas ainda exige correspondência comprovada com o arquivo gerado, adequação visual e autorização do titular.
3. **Revisão factual por versão:** conferir divergência do fabricante no processo Anatel, datas/status comercial atualizados, extrapolações nas pesquisas e originalidade no comparativo.
4. **Verificação visual de 390 px / 1440 px** dos rascunhos finais e testes reais do Gate Editorial Único no caminho WordPress, com bloqueio de publicação sem parecer aprovado por versão. O CI anterior não substitui estes testes de comportamento real.
5. **Homologação MKT-RSS → rascunho WordPress atual, ponta a ponta:** os rascunhos foram inspecionados/editados via conector WordPress, mas isso não demonstra que o executor MKT-RSS encaminhou a mesma versão com todos os metadados e aprovações; não inferir e2e completo.

## Decisão operacional

Os quatro pilotos continuam como rascunhos. Nenhum parecer automatizado, caderno ou status verde de workflow autoriza publicação. Quando o revisor externo entregar notas justificadas, confrontar as versões com as fontes, resolver imagens e comprovar o Gate real, atualizar este checkpoint por evidência, sem instalar outro executor, staging ou serviço pago.

## Gate Editorial — conferência de instalação em produção (somente leitura)

Em 2026-11-10, a listagem autenticada de plugins de `conexotech.com.br` registrou:
- **Conexo Editorial Gate (controlado)**, `conexo-editorial-gate/conexo-editorial-gate`, versão **0.1.0-rc5**, **ATIVO**.
- **Conexo HMAC Vault (provisao segura)**, `conexo-hmac-vault/conexo-hmac-vault`, versão **0.1.0**, **ATIVO**.
- Uma instalação MU-plugin intitulada `Conexo Editorial Gate` permaneceu **INATIVA** (não confundir com a implementação controlada ativa).
- Rank Math SEO e Conexo Native SEO (controlado) 0.5.2 também estavam ativos, sem alteração nesta auditoria.

A confirmação do status **não demonstra** que o Gate ativo intercepta qualquer tentativa de `publish`, que mantém assinaturas por versão nem que há rollback funcional. **Não** tentar publicar conteúdo de teste na produção sem uma barreira comprovada, pois isso poderia colocar o artigo no ar. A prova WordPress isolada existente no GitHub usa outro código MU-plugin; não pode ser extrapolada automaticamente para a implementação controlada rc5 em produção.

## Imagem editorial do guia (somente inspeção)

Na Biblioteca pessoal há imagem gerada em conversa, nome `Teclado inteligente no smartphone.png`, com 1672×941 px e 1.746.051 bytes (SHA-256 local `3db33303f9e6dd5d418da7792b9ff81750bc41001bddfc349158c52e5d7b3de1`). Metadados do WordPress para mídia #9799 apresentam mesmas dimensões e tamanho de arquivo. A imagem representa teclado **genérico estilizado sem textos**, não tela real do iOS; adequação temática visual preliminar positiva. As semelhanças de metadados **não são prova de bytes idênticos**, pois o hash do arquivo remoto não foi obtido, e não são atestado automático do titular. O direito de uso definitivo ainda requer comprovação de correspondência e confirmação do proprietário.


## Integração MDA AUTO — complemento técnico (PR #86)

Em 2026-11-10, o [PR #86](https://github.com/rmsports33/MKT-RSS/pull/86) foi integrado na master (merge beb85359b467ce0cb39f0368c57ca8577a2d9c97), após CI com **1.104 testes aprovados, 1 ignorado, 11 subtestes e 52 testes do redator**, além de validação editorial Conexo OS verde.

O adaptador mkt_flow_p0/editorial_voice_adapter.py opera **na redação e crítica existentes**. Não altera o briefing de seis campos, o hash do DNA, a permissão de publicar, o WordPress ou as fontes dos rascunhos atuais. É seleção de abordagem e movimentos intelectuais, **não** nova autoria. A documentação técnica é [EDITORIAL_MDA_ADAPTIVE_VOICE_20261110.md](EDITORIAL_MDA_ADAPTIVE_VOICE_20261110.md).

| Piloto real | Lente prevista ao reescrever sob o mesmo briefing |
|---|---|
| Guia #9798 | didático-prática: sintomas, escolhas reversíveis, consequências |
| Notícia #9635 | investigativo-documental: homologação regulatória vs. disponibilidade comercial |
| Análise #9687 | analítico-crítica; científico-explicativa somente se o recorte do briefing for explicitamente pesquisa/estudo |
| Comparativo #9681 | comparativo-decisória: critérios, trade-offs, decisão condicional |

Essas lentes são uma **previsão de roteamento por gênero, não prova de aplicação nos rascunhos atuais**. O caderno privado de avaliação A–E foi complementado com a rubrica MDA: função de cada seção, progressão, uso das fontes, contradições e fechamento. **Não houve novo A/B gerado**, chamada Groq, aceitação humana, concessão de direitos de imagem ou publicação WordPress por este PR. Para comprovar ganho real, comparar versões completas com as mesmas fontes e revisor humano independente, preservando o conteúdo privado e a chave das versões em locais separados.
