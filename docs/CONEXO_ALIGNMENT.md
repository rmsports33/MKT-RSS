# Aplicação das diretrizes Conexo OS

Data: 2026-10-26. Núcleo: [diretrizes integradas](https://github.com/rmsports33/conexo-os/commit/ec190d6b6c62df3235905499ee84eeb75ad9507d).

## Aplicação

- AGENTS.md encaminha ao contrato operacional, política de execução, tarefas e DNA reconciliado.
- Pesquisa de ferramentas passa a depender de lacuna real; prioridade para reutilização e entregas do ConexoTech.
- O prompt RSS usa voz inteligente/acessível, autoria correta e comprimento proporcional às evidências, sem exigir 500–800 palavras.
- O redator vendorizado preservado recebe os mesmos ajustes de identidade e exemplos monetários são removidos; não se torna fonte canônica do contrato.
- O bloqueio factual e os adaptadores já desenvolvidos no PR #18 são preservados: nenhuma saída do pipeline RSS autoriza escrita WordPress.

## Evidência executada

Python 3.12, validação local:

```bash
python -m pytest tests/test_m05* tests/test_fundational_editorial_flow.py tests/test_vendor_editorial_identity.py tests/unit/test_custo_real.py tests/unit/test_pipeline_rss_gate_p0.py tests/unit/test_pipeline_rss_p0.py tests/unit/test_rewriter_p0.py tests/unit/test_content_filter_p0.py tests/unit/test_content_filter_produto_p0.py tests/unit/test_comparativo_contract_p0.py tests/unit/test_comparativo_flow_p0.py tests/unit/test_publicar_comparativo_p0.py tests/unit/test_format_p0.py -q
```

Resultado: **240 passaram**, zero falhas. Escopo direcionado; não é toda a suíte do repositório.
Os quatro casos novos de fonte→HTML exercitam rewriter, JSON, atribuição, formatação e gates reais com captura e LLM simulados, connect/connect_ex bloqueados e credenciais fictícias. Testam saída sem alertas, número inventado, falsa alegação de teste próprio e falha de captura. Nenhum cria rascunho remoto.
Dois casos adicionais verificam identidade no consumidor vendorizado.

Revisão técnica independente por agente: 88 testes do recorte inicial aprovados e bloqueio incondicional WordPress conferido; mais 64 testes de identidade vendorizada e contratos/fluxo de comparativos aprovados após o último ajuste. Não constitui revisão humana.

## Limites e continuidade

- A compatibilidade estrutural e a cobertura literal não provam factualidade semântica ou autenticidade de fonte.
- Pesquisa externa, resposta de LLM real e operação WordPress não foram testadas nesta entrega.
- O mínimo operacional herdado de 200 palavras na saída do RSS permanece; o prompt adaptativo não remove esse limite técnico.
- O renderer vendorizado mantém sua interface legada; não substitui EditorialContract v1.0 do bot-redator-artigo.
- Não há autorização de publicação pelo simples resultado dos testes. Próxima necessidade para liberar envio: certificação factual pós-IA e autorização específica de escrita.
- Drive V3/current.json, credenciais e agendamentos permanecem preservados.
