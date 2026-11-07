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
- [ ] Execução de suíte e correção de falhas.
- [ ] Adapter invocável pelo executor real autenticado e armazenamento privado do parecer.
- [ ] Piloto fim a fim do rascunho #9768 com readback e versionamento.
- [ ] Gate Editorial em execução impedindo toda rota de publicação sem evidência e aprovação.
