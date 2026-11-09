# Seleção editorial na nuvem, sem IA obrigatória — 09/11/2026

## Contrato e limites

MKT-RSS continua motor completo e único publicador RSS. Este módulo acrescenta
triagem antes da redação, não outro publicador. Pesquisa documental atribuída,
sem alegação de laboratório próprio. Um resultado candidato exige revisão humana,
fontes, direitos de mídia e autorização da versão nos gates já existentes.

`mkt_flow_p0/opportunities.py` usa apenas stdlib; não acessa rede, IA, DB ou WP.
Aceita no máximo 100 entradas/1 MiB em JSON ou CSV (campos aninhados em JSON).
Gêneros: oferta, rumor, noticia, review, comparativo, guia. Campos:

- `title`, `url` HTTPS, `kind`, `observed_at` ISO com timezone.
- Notícias: `event_at`, `published_at`; atualizar a página não renova o fato.
- Produtos: `products[]` com model, variant, market=BR, commercial_status,
  support_status, available_new, checked_at, source_url.
  active é declaração apoiada na fonte, não inferência pelo ano do modelo.
- Oferta: `offer` com price positivo, currency=BRL, url e checked_at.
- `evidence[]`: claim, nature (official/third_party_measurement/editorial_inference),
  source_url, locator e checked_at. Registro é rastreabilidade, não certificação.
- `demand`: source=trends|search_console, geo=BR, source_url, period_start,
  period_end, observed_at, points[{at,value,partial}]. Sete dias exatos, ao menos
  uma observação em cada dia, sem pontos parciais/futuros. Janela móvel, não
  `tail(120)`. Sinal zero é SEM_SINAL_NA_AMOSTRA, nunca 'ninguém procura'.
  Search Console mede apenas exposição do próprio site. Trends não mede volume.

TTL inicial, configurado no código e sujeito a ajuste editorial: oferta 6h,
rumor 24h, notícia 48h, demais 168h. Fato noticioso máximo 7d. Observação/fonte
vencida gera revisão; produto descontinuado/residual/indisponível ou suporte
encerrado exclui recomendação automática mesmo com sinal positivo de demanda.
Uma exceção editorial exige outro enquadramento e revisão, não desligar o filtro.

## Operação por navegador/celular

O botão Actions > Opportunity screening aceita caminho de arquivo já gravado
no repositório. Em repo público, nunca colocar rascunhos privados, dados pessoais
ou credenciais nesse arquivo. O workflow não exporta banco nem conteúdo: apenas
contadores. O job exige repositório público, runner Ubuntu padrão e confirmação
manual, sem artifacts/cache ou serviços pagos. A computação nesse caso é gratuita
segundo https://docs.github.com/en/billing/concepts/product-billing/github-actions.
Cópias privadas ficam impedidas de executar esse job. Não há serviço residente
nem Codespace obrigatório. O cron existente não depende de variável nova.

Em ambiente cloud temporário, via terminal do navegador:

```bash
python -S editorial_opportunities.py caminho/entrada.json --output relatorio-novo.json
python research_snapshot.py autocomplete 'produto vale a pena'
python research_snapshot.py trends 'produto A' 'produto B'
```

O primeiro comando independe de dependências instaladas. O segundo reaproveita
autocomplete existente, agora pt-BR/BR, sem transformar sementes em demanda.
O terceiro usa trendspyg opcional; ausente/indisponível é estado explícito.
Não instala pacote automaticamente, não chama navegador como fallback, não
repete em 429 nem usa proxies para contornar bloqueios. Snapshot bruto precisa
ser normalizado/conferido no contrato; nunca é candidato aprovado por si só.
CSV/JSON manual preserva operação sem esse provedor. API oficial de Trends
é alternativa apenas quando acesso estiver disponível, sem depender de alpha.

## Fila, persistência e recuperação

`fila_pautas.listar` acrescenta opportunity sem promover estado. RSS registra
apenas publicações datadas nas últimas 168h. O chamador pode exigir credenciais
Turso com CONEXO_REQUIRE_CLOUD_PERSISTENCE=1 antes da coleta. O daily preexistente
foi preservado integralmente para não alterar sua ativação/persistência sem
homologação. Seu upload legado de DB e possível fila efêmera permanecem uma
pendência operacional, não uma correção entregue nesta integração.

`queue_recovery.py export origem.db snapshot-novo.db` cria snapshot SQLite e
manifesto SHA256. `restore snapshot.db destino-novo.db --manifest snapshot.db.json`
recusa corrupção e sobrescrita. Testado com dados sintéticos, incluindo perda do
executor. Não exporta Turso: backup remoto exige acesso autenticado próprio.
Manter snapshots em destino privado autorizado; Git mirror não cobre mídia/DB WP.

## Disponibilidade e economia

Codespaces somente manutenção, mínimo de núcleos, timeout de inatividade e dados
persistidos antes de encerrar. Computação é core-hours; armazenamento também
consome franquia. Actions Linux curto, sem install pesado neste workflow, limite,
concurrency, cache e retenção proporcional. Não abrir SearXNG/RSSHub/servidor novo.
Agendamento é best effort: conferir última coleta e idade da fonte antes de usar.
Permissões financeiras/segredos só por canais de conta autenticados; jamais
copiar segredos entre projetos para resolver uma ausência de configuração.

## Homologação

Regressões: 7d completos, fontes indisponíveis, notícias expiradas, modelos
descontinuados, variante desconhecida, preço inválido, importação CSV, CLI -S
em diretório vazio e restauração sem perda. Testes simulados não provam Trends
real, continuidade do cron, faturamento ou publicação. Esses pontos continuam
pendentes até evidência operacional específica.
