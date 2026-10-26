# M05.5-B — Execução cloud-first e diagnóstico CI
Data: 2026-10-26. PR #20. Não publicar, não mesclar automaticamente.

## Evidência observada
- Commit anterior a correção: a4ee0ebb2474e8852ef637603f95951f66cb1663
- Editorial validation GitHub Actions run 40331243702: success, job 121600904045. Gate executou a lista de testes aprovados, não um ensaio real com LLM.
- CI geral GitHub Actions run 40331242952: failure, job 121600901588. Instalação de dependências: success. MKT-RSS tests: 519 passed em 10.54s. Testes do redator vendorizado: 51 passed, 1 failed.
- Falha exata: redator-artigo-blogs/tests/test_render.py::test_titulo_usa_marca; esperava texto legado 'Redação ConexoTech' no HTML. O renderer integrado usa author JSON-LD Person name 'Reinaldo Mendes'.
- Alteração pontual na branch de auditoria, commit bf5297a5cfc142c3980dc8d04a39723d1d951209: teste passou a exigir autoria humana correta e ausência do legado. Código de produção não foi modificado. A execução remota pós-correção ainda exige novo resultado do CI.

## Não realizado
- Não foi feita chamada de IA real, pois provedor autorizado, credenciais disponíveis no executor e orçamento concreto não foram confirmados.
- Não foi executado um fluxo source→LLM→HTML real com fontes acessadas pelo extrator do projeto.
- Não foram executados os casos negativos N1–N7 com dados reais nesta etapa; a CI editorial apenas executou testes já existentes com mocks.
- Não houve revisão humana/independente da prévia.
- Não houve WordPress, merge, deploy, ativação de credenciais ou nova automação.

## Decisão
Manter verificação factual NAO_VERIFICADO e bloqueio de escrita WP.
Próximo passo seguro: confirmar CI pós-correção, produzir execução real em ambiente cloud existente com orçamento permitido e emitir matriz claim→source para título, corpo, SEO, JSON-LD e campos derivados. Separar revisão independente antes de qualquer rascunho.
