# Decisão operacional Binance — checagem documental e fronteira WordPress (14/11/2026)

**Estado:** PREPARADO PARA NOVA REVISÃO, não publicado. Este documento não equivale a certificado factual do Gate.

## WordPress autenticado: fatos observados pelo conector

- Site consultado: `conexotech.com.br`.
- **Post 9708:** `draft`, título "iPhone Duo Nano Texture: críticas e resposta da Samsung", slug `iphone-duo-nano-texture-criticas-samsung`. Não é Binance. **Não atualizar esse post.**
- **Post 9744:** `publish`, título "Binance sofre ataque de US$ 6,36 bilhões; grupo ligado à Coreia do Norte é suspeito", slug `binance-ataque-hacker-636-bilhoes-coreia-do-norte`. Conteúdo anterior já publicado, não substituir.
- Pesquisa pelo slug `binance-cobertura-roubo-cripto-2026-revisao` não retornou nenhum post. **Não foi criado rascunho.**
- Biblioteca de mídia: imagem Binance existente ID 9746, associada ao artigo publicado 9744, com título "Ataque à Binance — ilustração ConexoTech". Sua licença não foi confirmada nessa consulta; **não reaproveitar como nova capa automaticamente.**
- Conector WordPress suporta leitura/atualização de mídia e posts; novo post e upload de imagem exigem associação controlada ao conteúdo de versão exata, não escrita em artigo já publicado.

## Quatro afirmações: documentação de suporte, não aprovação

| ID do contrato | Ponto apurado | Referência pública | Estado |
| --- | --- | --- | --- |
| extra_1_1 | Reuters 14/11 relata 95% de reposição no contexto da retomada em 87 redes; a Binance espera normalizar as restantes | https://www.reuters.com/legal/government/binance-targets-full-reopening-withdrawals-by-next-week-2026-11-14/ | FONTE_INSPECIONADA; CLAIM_PENDING |
| extra_2_1 | Reuters 31/10 registrou 90% reposto com recursos próprios e 10% restante de tokens menos líquidos | https://www.fidelity.com/news/article/company-news/202610311134RTRSNEWSCOMBINED_L6N46H03L_1 | FONTE_INSPECIONADA; CLAIM_PENDING |
| extra_3_1 | AP descreveu roubo estimado em US$ 6,3 bi e congelamentos; **atualização da AP de 12/11 demanda distinção temporal e jurídica** | https://apnews.com/article/binance-cryptocurrency-security-hack-north-korea-550e9b876550f71f07098494fe735beb | FONTE_INSPECIONADA; CLAIM_PENDING |
| extra_4_1 | Tecnoblog 14/11 atribui à Binance anúncio de 100% de recomposição, não recuperação integral dos tokens roubados | https://tecnoblog.net/noticias/r-34-bilhoes-binance-cobriu-100-do-prejuizo-do-maior-roubo-de-cripto-da-historia/ | FONTE_INSPECIONADA; CLAIM_PENDING |

### Atualização factual indispensável antes do Gate

Em 12/11, a Associated Press noticiou que autoridades americanas afirmaram ter **obtido autorização judicial para apreender ou restringir mais de US$ 1,2 bilhão**, dentro de mais de US$ 2,7 bilhões congelados por governo e setor privado. **Isso não representa restituição definitiva aos clientes ou recuperação integral da soma roubada.** A formulação atual do artigo usa referência inicial a cerca de US$ 3 bilhões localizados/congelados; na próxima versão deve distinguir data, valores congelados, valores sob autorização judicial e propriedade final ainda pendente.

Fonte: https://apnews.com/article/fbi-binance-cryptocurrency-theft-north-korea-41be4834083e596a8facfd719f851cae

### Preflight para o próximo pacote

1. Incorporar a atualização AP ao Markdown **em nova versão** e invalidar todo parecer textual amarrado ao hash anterior; reavaliar as passagens afetadas.
2. Transformar as quatro alegações em pares `claim -> evidence` com trecho atribuível presente no texto, consulta pública e data da fonte. **Nenhum `evidence_ids` deve ser preenchido como aprovado antes da verificação e do contrato do Gate.**
3. Usar os três links internos verificados pelo WordPress; não exigir repetição de checagens de existência dos mesmos links a cada execução.
4. Associar a imagem Unsplash já validada por hash (desktop `b5ba5abd...`) ao **novo** rascunho apenas quando a versão correta do artigo estiver preparada; não reutilizar a imagem 9746 ou o post 9708 por coincidência textual.
5. Não publicar; `human_acceptance=PENDING`, `publication_authorized=false` até aprovação explícita e Gate autenticado.

## Fronteiras mantidas

O `PASS` da revisão substantiva atesta uma avaliação textual assistida; não concede certificação factual, direitos de mídia WordPress ou permissão de publicação. Evitar novas importações privadas para mera atualização do resumo de pendências.

## Consolidação editorial final (14/11) — atualização AP verificada

A matéria em `docs/ARTIGO_BINANCE_REVISAO_2026-11-14.md` recebeu a notícia AP de 12/11: congelamento de **mais de US$ 2,7 bilhões** e, **dentro desse valor**, autorização judicial de apreensão/restrição sobre **mais de US$ 1,2 bilhão**. Esses montantes não são cumulativos nem comprovam devolução aos clientes. Fonte original: https://apnews.com/article/41be4834083e596a8facfd719f851cae ; cobertura AP republicada: https://abcnews.com/Technology/wireStory/fbi-us-seized-12-billion-worth-cryptocurrency-stolen-138094651 .

- Novo SHA256 **exato do corpo Markdown** (após remoção do título e do aviso operacional): `1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60`.
- O parecer assistido vinculado a esse SHA foi atualizado apenas no critério de suporte à decisão e limites das fontes; **não há parecer humano, aprovação factual ou autorização de publicação**.
- O importador usará a AP de 12/11 como uma das quatro fontes indicativas, com o claim respectivo **PENDING**; três links internos publicados foram confirmados por consulta autenticada ao WordPress.
- Teste focado alterado para exigir a distinção jurídica entre os valores; executar somente `tests/test_binance_review_integration.py`, não a regressão geral.
- Mídia: manter a capa Unsplash já preparada em `~/.local/share/conexo-os/imagens/binance`; os dois crops têm hashes documentados. **Não usar a mídia antiga 9746 sem verificação de direitos.**
- O plugin Gate empacotado disponibiliza `conexo/v1/editorial/write`, mas o conector WordPress disponível não expõe esse endpoint arbitrário. **Não contornar o Gate com `wpcom_mcp_posts_create`** enquanto os 4 claims estiverem pendentes.
- Resultado esperado de importação: **uma única nova pasta privada**, não atualização do pacote v2 `binance-revisao-ce674e255211`. A publicação no WordPress permanece bloqueada até contratos e aprovação da versão.

## Comprovação operacional — importação final de 14/11/2026

Execução relatada diretamente pelo operador em PowerShell/SSH Hostinger:

```text
Ran 2 tests in 0.018s
OK
status: REVIEW_ONLY_IMPORT_CREATED
path: /home/u401421381/.local/share/conexo-os/handoffs/binance-revisao-48f1ea5be313
version_sha256: d2ccb99e2dbe0dbc999a4b8e1fdd49d089c9299c679f5cb6200edc5db6e00fd2
content_sha256: 1969799ce2c4a1b6ad629eec62c39095ac58418695bab2f3f53efefe57448b60
editorial_readiness_status: ENRIQUECIMENTO_PENDENTE
substantive_review_status: PASS
voice_application_status: ASSISTED_ADAPTED
image_research_status: PREPARED_LICENSED_IMAGE_INSTALLED
wordpress_written: false
publication_authorized: false
pending:
  - imagem_destacada_com_direitos_pendente
  - human_factual_approval
  - authenticated_wordpress_gate_and_human_version_acceptance
```

A importação foi concluída e os dois testes focados passaram. **A lista de pendências resumida não prova que os quatro claims foram aprovados:** o contrato de evidências permanece sujeito ao Gate e à revisão humana. Não reimportar apenas para corrigir relatórios, não modificar post 9708 nem post publicado 9744, e não publicar sem autorização específica para este hash.

## Execução direta WordPress e evidências (14/11/2026)

- **Capa realmente enviada à biblioteca de mídia do WordPress de produção:** ID **9892**, arquivo `2026/11/conexotech-binance-cobertura-ataque-2026-capa.jpg`, 1440 × 810, alt e crédito cadastrados. Reconsulta autenticada confirmou `post=null`; portanto ainda não é imagem destacada de um rascunho.
- Fonte/licença pública revisitada: https://unsplash.com/photos/a-rack-of-servers-in-a-server-room-2JJ3wBHu4_0 (Kevin Ache, Unsplash License); crop original SHA-256 `b5ba5abd2bb4810eb3641d9c88a7e0d9108f401cb6a9567a44d8ce4f9e1d2d74`.
- **Evidências pré-revisão:** `docs/BINANCE_CANDIDATOS_EVIDENCIA_FINAL_2026-11-14.json` lista 4 claims com trechos literais presentes na versão, URLs, interpretações e estado `SOURCE_CHECKED_ASSISTED_PENDING_HUMAN`. Não usa `status=PASS` ou `evidence_ids` confiáveis do Gate.
- Consulta autenticada `wpcom_mcp_posts_list` pelo slug `binance-cobertura-roubo-cripto-2026-revisao` confirmou **nenhum rascunho** correspondente.
- O código Gate em `conexo-editorial-gate/includes/conexo-editorial-gate-core.php` expõe `POST /conexo/v1/editorial/write`, com `intent=stage` para criação e assinatura; o conector WordPress atual permite `wpcom_mcp_posts_create`, mas **não** a rota customizada do Gate. Não usar escrita genérica para desviar do Gate.
- O broker `/editorial/broker/write` não aceita criação de draft (`intent` restringe-se a publish/schedule) e exige executor e revisão independentes.
- **Resultado:** uma nova capa (mídia WordPress 9892) foi criada; nenhum artigo ou rascunho foi escrito; não houve aprovação factual/humana/publicação. A única operação restante para criar o draft precisa ocorrer via executor autenticado do Gate, com o pacote exato versionado, IDs de evidências assinados pelo revisor humano e mídia 9892.
