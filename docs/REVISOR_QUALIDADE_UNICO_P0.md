# Revisor Editorial Único — P0

Implementação inicial: `mkt_flow_p0/revisor_qualidade_unico.py` (`conexo-article-quality/1`).

**Estado: módulo testável em branch; não ligado automaticamente ao WordPress nem ao Gate em produção.** O resultado `APTO_PARA_APROVACAO` não concede permissão de publicação.

## Contrato de entrada

- `post`: saída de `wpcom_mcp_posts_get(id, context="edit")`, dados brutos de um artigo real. Os campos mínimos são id, title, content, excerpt, slug, categories e featured_media.
- `media`: `wpcom_mcp_media_get(id=featured_media, context="edit")`, com id, alt_text e description incluindo documento de licença.
- `fontes`: objetos `{url, verificada, alegacoes: [...]}` provenientes de pesquisa identificada (não de texto inventado).
- `corpo_original_fonte`: texto original verificável para o detector pós-IA já existente; quando ausente, o check de alegações fica `NAO_VERIFICADO`.
- `evidencias`: avaliações independentes por chave `licenca_imagem`, `revisao_substantiva`, `visual_390`, `visual_1440`: cada uma exige o SHA-256 da versão (`fingerprint`), revisor, `aprovado=true` e URLs/identificadores de provas não vazios. Fotografias com URL de licença nos metadados são **declarações**, não prova de direito.

## Saída

`avaliar_artigo(...)` devolve fingerprint por campos editoriais, checks de estrutura/qualidade, bloqueios, pendências, `APTO_PARA_APROVACAO | REVISAO_NECESSARIA | BLOQUEADO`, sem escrita. `verificar_versao(parecer, post_atual)` reprova conteúdo/metadata alterados. A data `modified` isolada não invalida por si só; o hash protege os campos efetivos.

A revisão humana de fontes, alegações, links pertinentes, aparência e uso de imagem continua obrigatória. O check simples de HTML **não é validador DOM**; o check SEO **não é uma nota de Google/Rank Math**; check `SEM_ALERTAS` de alegações não comprova factualidade.

## P0 — integração operacional restante

1. Adaptar o executor autorizado do Núcleo Editorial ChatGPT-first para buscar WordPress/MCP e registrar o parecer e suas evidências de forma privada. Não adicionar senhas/tokens ao repositório ou arquivos públicos.
2. Exigir `verificar_versao` e revisão humana independente antes da aprovação no Gate Editorial Único. Publicação segue autorização humana específica; chamada WordPress direta pode contornar código que não está instalado no runtime, portanto não declarar proteção em produção sem teste.
3. Exercitar rascunho real #9768 sem publicar; testar mudança de versão, fonte não rastreada e falta de licença. Conferência 390/1440 apenas com capturas verificáveis.
4. Validar testes `python -m unittest tests.test_revisor_qualidade_unico -v` em executor cloud, juntamente com regressão existente. Sem dependência de Python no computador do usuário ou staging obrigatório.

## Critérios de aceite

- [x] Contrato e validadores fail-closed no MKT-RSS.
- [x] Testes unitários adicionados (resultados da execução ainda por conferir).
- [x] Suíte em runner cloud: 643 testes principais e 52 adicionais aprovados (run 42393309902).
- [x] Adapter WP REST autenticado implementado, com cache de parecer em SQLite privado e submissão explícita ao Gate; integração da credencial no executor hospedado real ainda pendente.
- [ ] Piloto fim a fim do rascunho #9768 via adapter cloud (somente leitura WordPress MCP já comprovada, mas o módulo novo ainda não foi invocado contra a produção).
- [ ] Gate Editorial em execução impedindo toda rota de publicação sem evidência e aprovação.

## Executor cloud sem Python local

Com credenciais WordPress guardadas exclusivamente no secret store da execução confiável (nunca em GitHub público, logs, prompts ou PR), usar:

```bash
python -m mkt_flow_p0.wp_quality_executor --post-id 9768 --evidence-file /secure/9768.json --db /secure/conexo-quality.sqlite
```

Variáveis `CONEXO_WP_URL`, `CONEXO_WP_USER`, `CONEXO_WP_APP_PASSWORD` vêm do runtime autorizado. O relatório é gravado em arquivo com permissão 0600; em runner efêmero, **não equivale a armazenamento durável entre jobs**. Para uma aprovação APTO, o `--submit-quality` enviado com a identidade WordPress de um revisor independente persiste o relatório em `wp_options` privado, desde que o Gate novo esteja instalado. A submissão **não** chama publicar nem agendar. Um gate inativo ou uma credencial ausente não são contornados.

No site de produção, o conector WordPress listou `Conexo Editorial Gate` como **inactive** na leitura de 07/11/2026; não presumir proteção ativa pelo status do CI. Testes completos de gate na [PR #62](https://github.com/rmsports33/-site-conexotech/pull/62), CI WordPress+MySQL: [run 42393624254](https://github.com/rmsports33/-site-conexotech/actions/runs/42393624254), 53 testes PHP + 32 verificações WP, sem deploy.


## Correções de segurança e coerência — 11/11/2026

A revisão do código antes de integrar este PR constatou que **ausência de alerta automático não equivale à confirmação factual**: o detector pós-IA é numérico e superficial. Agora alegações somente podem receber `VERIFICADO` se houver uma evidência humana identificada e vinculada ao fingerprint da versão, mesmo quando o detector retorna `SEM_ALERTAS`. Quando o detector encontra contradição numérica, o estado continua `REPROVADO`. Isso ainda NÃO autentica sozinho a identidade do revisor: o Gate WordPress deve executar a verificação real de permissões.

A regra de links foi reconciliada com o DNA ConexoTech: **até três links internos genuínos**, e nenhum mínimo artificial. Zero links pode ser aceitável quando não houver conexão editorial real, mas depende do atestado humano de pertinência/ausência e da mesma versão. Mais de três links bloqueiam a prontidão.

O cliente de revisão WordPress agora exige origem exata `https://conexotech.com.br`, **não segue redirects** que poderiam expor a Application Password, recusa posts fora de `draft` e reprova versões alteradas antes de persistir ou enviar parecer.

As verificações internas continuam **somente pré-revisão**; um relatório `APTO_PARA_APROVACAO` não deve equivaler a aceite de um revisor independente, nem libera escrita. O subprocesso ainda deve ser integrado à única rota do Gate já ativa, sem duplicar aprovação ou criar executor concorrente.

O PR permanece em **draft** até resolver o contrato entre os formatos `conexo-article-quality/1` e o plugin 0.1.0-rc5 da Hostinger, testar leitura real apenas de posts draft e comprovar se as evidências são verificadas por identidade e por versão antes do Gate, sem qualquer publicação. Testes sintéticos são necessários, mas insuficientes para homologação de produção.

## Compatibilidade RC5 — 11/11/2026

Comparação com a cópia auditada do plugin na branch `rmsports33/-site-conexotech:audit-active-gate-rc5-20261111`, árvore `5f549f2a2c6da6cc6f2eb92d5e3bef7658cffe5a` (core blob `fe51fdc6b72b87030ffe7abaec9f849ab0e2a756`). Não representa nova inspeção da Hostinger.

Os 13 checks e os endpoints snapshot/quality/record são compatíveis. O hash do parecer Python continua distinto do hash RC5. Antes de enviar, o adaptador agora reconstrói o snapshot RC5 a partir dos campos REST brutos, normaliza data GMT e ordem das categorias, confere conteúdo e hash retornados, relê o draft e exige confirmação com post_id e snapshot_sha256 idênticos. Autor, tipo e data GMT passam a compor o fingerprint: pareceres anteriores precisam ser refeitos. Não há fallback para HTML rendered na submissão.

Identidade autenticada e permissões continuam verificadas pelo servidor; o campo reviewer do JSON não autentica uma pessoa. O cliente permanece no modo independent padrão. O modo owner autorizado já existente no RC5 continua pela interface humana própria; este patch não o implementa no CLI nem inventa aceite humano. Parecer registrado não é aprovação nem publicação.

Limites remanescentes: Gate exige evidência não vazia para cinco checks, mas não apura fatos nem valida sozinho os documentos de origem; o cliente exige atestados versionados também para alegações e links. Não tratar uma string de referência como prova factual independente. O vínculo do servidor é ao snapshot RC5, e não a uma recomputação do fingerprint Python. Testes locais são sintéticos; faltam piloto autenticado somente de rascunho, readback privado e aprovação humana real. Nenhuma mudança PHP/produção integra este patch.

Validação local do revisor, executor, voz MDA e regressões numéricas: 46 testes e 25 subtestes aprovados; diff sem erros. Contraprovas cobrem divergência do snapshot, hash inválido/incorreto, troca de autor/data/status na última leitura e confirmação de outro post/versão.

## Piloto autenticado somente leitura — 11/11/2026

Concluído o piloto pela conexão WordPress MCP: duas leituras context=edit do post #9798 e uma leitura da mídia #9799; os dois snapshots do post foram idênticos e mantiveram status draft. O motor review_once consumiu essas leituras capturadas localmente, salvou um parecer em SQLite 0600 e confirmou a persistência por SELECT. Não houve credencial transportada para o Python, HTTP direto do WPClient, chamada ao endpoint Gate, submissão de parecer, aprovação ou escrita WordPress. Portanto isto comprova MCP autenticado → motor local → registro privado, não integração HTTP autenticada direta nem armazenamento durável hospedado.

O antigo alvo #9768 já estava publicado na leitura atual. O motor recusou essa captura real antes de criar o banco, corrigindo a premissa antiga de usá-lo como draft. Não alterar status de artigo publicado para testar.

Resultado editorial final do #9798: BLOQUEADO pela categoria padrão [1]. Pendências: licença/proveniência da imagem, fontes, alegações, links internos, revisão substantiva e conferências 390/1440. Não foram fornecidos atestados humanos: campos ausentes permanecem pendentes mesmo quando existem referências no corpo. O parecer privado não foi versionado nem transformado em autorização. Capturas e SQLite permanecem no executor efêmero; não foi comprovado arquivo durável externo.

Falha de classificação corrigida: uma ilustração declarada como gerada por IA não precisa inventar URL de licença de banco. Para esse caso, o atestado licenca_imagem exige tipo_origem=gerada_ia, reviewer, fingerprint, aprovado=true e referências de proveniência/uso verificadas; declaração na mídia sozinha permanece NAO_VERIFICADO. Sem origem declarada ou ALT, o bloqueio permanece. Não foi criado atestado humano para a mídia real.

Validação da correção: 48 testes e 25 subtestes locais aprovados. Continuação editorial depende de categoria adequada e evidências reais; o piloto técnico de leitura está concluído.
