# Evidência privada de demanda por pauta — 09/11/2026

## Resultado implementado

Pacote imutável com ID/URL da pauta, consulta explícita, série original completa
(incluindo pontos parciais), contexto comparativo, normalização, horário original
e registro da revisão da consulta. Hash SHA256 cobre todo o pacote. Replay
recalcula a normalização original e também avalia a atualidade no momento atual.
Série vencida não recupera elegibilidade só porque passou anteriormente.

SHA detecta corrupção, não assinatura/autoria confiável. Trocar termo/série sem
atualizar o hash é detectado; recalcular somente hash sem atualizar avaliação
também é recusado. Um agente que reconstrua um pacote inteiro pode gerar novo
hash: isso NÃO autentica origem, revisão ou factualidade. Aprovação editorial
continua nos gates existentes, nunca neste armazenamento.

Revisão padrão PENDING. Campos opcionais reviewer/reason/reviewed_at registram
DECLARED_NOT_AUTHENTICATED, vinculados ao pacote; não fabricam revisão humana,
nem alteram topic_relevance_verified/publication_authorized. Prova automática
usa PENDING. Reavaliar uma consulta alterada exige novo pacote/versionamento.

## Armazenamento reaproveitado

- JSON local em destino privado autorizado: criação exclusiva, modo 0600,
  leitura limitada a 512 KiB. Opera com Python -S, sem IA ou rede. Diretório cloud
  efêmero não é persistência durável por si só.
- Turso já existente, opt-in: tabela aditiva `conexo_demand_evidence_v1`, ID por
  hash, ID da pauta e JSON privado. INSERT OR IGNORE com leitura exata, sem
  UPDATE/DELETE; erro de escrita desconhecido exige reconciliação por digest,
  não retry cego. Falta de configuração não gera fallback SQLite.
- URL libsql exata e host .turso.io explicitamente permitido por
  CONEXO_DEMAND_TURSO_ALLOWED_HOST. Segredo existente somente em secret manager.
  Não copiar credenciais. Importar o módulo não conecta nem cria tabela.
- `references(pauta_id)` consulta até 100 IDs em leitura; `get(digest)` valida
  integridade/replay antes de devolver o pacote; `replay` exige ID e URL esperados.
  Não integra automaticamente a consulta à listagem diária ou seleção da fila.

Não persistir corpos de artigo, prompts, cookies ou consultas relacionadas. O
construtor seleciona apenas contexto e campos da série. A prova usa a identidade
canônica da fila, mas não registra pauta e não afirma que uma linha exista:
queue_row_verified=false. Associar a uma linha produtiva requer consulta existente
verificada; este passo não altera sua nota/estado nem impõe bloqueio novo.

## Operação portátil

Em terminal de nuvem autorizado, com arquivo privado de envelope Trends:

```bash
python3 -S demand_evidence.py pack --input trends.json --pauta-id ID_EXISTENTE --pauta-url https://exemplo.org/pauta --query 'consulta revisada' --output evidence-private.json
python3 -S demand_evidence.py replay --input evidence-private.json --pauta-id ID_EXISTENTE --pauta-url https://exemplo.org/pauta
```

Para registrar declaração de revisão, pack aceita conjuntamente --reviewer,
--review-reason e --reviewed-at ISO com timezone. CLI imprime somente resumo;
conteúdo completo fica no arquivo privado. Não inserir arquivo no Git público.

## Prova real e limites

Issue exata do proprietário `[demand-evidence] guardar serie e reproduzir` executa
somente no MKT-RSS público original. Primeiro job: testes, uma leitura do RSS,
uma consulta Trends BR de sete dias para o primeiro título exato e uma gravação
de evidência no Turso homolog existente. Segundo job: recupera pelo digest,
confere associação por ID/hash da URL, reconstrói avaliação sem Trends, IA,
artifact ou DB local. Não exige navegador/PC. Só hashes, contagens e flags no log.
Ambos usam rss-homolog; proteções do ambiente não podem ser contornadas.

A prova não aprova o título como consulta ideal e não inventa revisão. Não é
backup da fila, não toca suas tabelas e não ativa cron. Staging segue desativado;
WordPress/Rank Math/publicação não são alterados. Não há serviço/contratação nova.

59 testes direcionados passaram: 39 com python -S e 20 regressões de fila,
pesquisa e workflow. Dez testes novos cobrem replay em novo processo, corrupção,
associação errada, dados vencidos, revisão declarada, arquivos privados/exclusivos,
SQL parametrizado/idempotente, escrita incerta e guardas do workflow. SQL local
é fixture, não prova de Turso; execução externa deve ser registrada separadamente.
