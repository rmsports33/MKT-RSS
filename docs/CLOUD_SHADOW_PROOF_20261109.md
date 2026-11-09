# Prova incremental cloud — 09/11/2026

Complementa o núcleo de oportunidades já integrado. Não altera `daily.yml`, fila,
estados editoriais, WordPress ou o publicador. Não adiciona cron, serviço,
artefatos ou cache. Runner padrão somente no repositório público.

## Implementado

- `opportunity_shadow.compare`: diagnóstico aditivo e limitado a 100 entradas,
  sem promover estado nem alterar os objetos fornecidos.
- `scripts/cloud_editorial_probe.py`: duas provas separadas e limitadas.
  - Persistência: reutiliza o adaptador de traces e o segredo existente no
    environment `rss-homolog`. Grava um único envelope de metadados identificado
    por run/attempt; verifica a igualdade imediata e em outro job/runner, sem
    SQLite local ou artifact. Não armazena corpo de artigo e não testa a fila
    produtiva. Host e URL de homologação são exatos. Falha não gera retry.
  - Fonte real: uma requisição ao feed Tecnoblog já cadastrado, TLS padrão,
    timeout 8 s, sem redirects e corpo limitado a 1 MiB. Compara até três
    candidatas e salva JSON temporário no executor. Resumo público contém só
    contagens, motivos, fonte, horário e hash da resposta. Não presume demanda,
    data do fato, direitos, aprovação ou factualidade.
- Workflow por abertura de Issue com título exato
  `[cloud-probe] validar homolog e RSS real`, apenas pelo proprietário no
  repositório público original. Input de Issue nunca vira comando de shell.
  O job de regressões antecede rede; RSS não depende de segredo Turso.

## Validação local

25 testes com `python3 -S` (6 novos + 19 existentes); 8 regressões adicionais
(Turso trace e preservação dos workflows). Total 33, sem somar reexecuções.
Fixtures não são comprovação de serviço externo. `daily.yml` permanece idêntico.

## Critérios de conclusão externa

Registrar run, SHA e resultados reais. Se o segredo faltar, estiver inválido,
o environment exigir aprovação ou a rede negar acesso, registrar o bloqueio
sem inventar sucesso nem contornar a proteção. Uma prova de metadados bem
sucedida não homologa automaticamente persistência da fila produtiva.

## Continuação

Depois da prova: integrar diagnósticos à consulta de fila em leitura e comparar
amostra real com demanda BR de sete dias. Somente dados verificáveis permitem
promover critérios. SEO live continua separado: deve usar o transporte pinned
especificado e interromper em DNS/TLS/robots; este coletor RSS não o substitui.
