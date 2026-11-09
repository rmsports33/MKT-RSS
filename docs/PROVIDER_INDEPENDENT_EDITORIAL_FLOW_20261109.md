# Correção de integração editorial — 09/11/2026

## Causa comprovada

A entrega do guia foi salva em Markdown no Conexo OS com revisão assistida, mas
não ingressou no importador MKT-RSS já existente. Foi uma falha operacional desta
sessão: documento de pesquisa/redação foi apresentado como etapa concluída sem
recibo dos módulos. O importador também era isolado: persistia envelope, mas seu
CLI não chamava core/renderização/SEO/prontidão. O CLI principal só oferecia
handoff-only a partir de RSS e redator Groq, exigindo fonte/limit=1. Não havia
entrada equivalente para texto pronto de editor humano ou qualquer provedor.

## Correção implementada

O CLI principal agora aceita entrada editorial pronta:

```bash
python3 -S pipeline_rss.py --import-article entrada-privada.json --handoff-only --handoff-dir saida-privada-nova --genero guia
```

O CLI `python3 -S -m mkt_flow_p0.editorial_import` também chama o processamento
integrado. O helper baixo nível anterior continua compatível e não é uma etapa
completa; sua existência não autoriza chamar um artigo de processado.

Reutiliza funções existentes: import/identidade, core offline, formatação, SEO,
contrato SEO consultivo, prontidão, alertas numéricos/teste próprio, adaptador
factual e trace. Saídas: pacote versionado, HTML noindex de prévia, fragmento WP,
metadata/Markdown, diagnósticos e trace. Diretório exclusivo 0700 e arquivos 0600,
sem sobrescrever versão ou reaproveitar aceite. Falha de validação não cria saída.

Não importa SDK/provedor, busca RSS, chama rede, abre DB/fila ou escreve no WP.
Credenciais de IA/WordPress não são necessárias. Flag de publicação/RSS misturada
com importação é recusada. Conteúdo pode vir de editor humano, modelo opcional
ou ferramenta diferente; isso torna a preparação independente do provedor, não
inventa autoria/revisão nem promete redação original sem autor/insumos.

O gerador Groq do RSS continua intacto. Não foi criado publicador concorrente,
trocado Rank Math ou ativado staging. Operação WordPress supervisionada mantém
seus controles; este comando só prepara pacote/HTML, nunca é endpoint de escrita.

## Correções verificadas com o caso real

- Referência de palavras por gênero mudou para aviso consultivo; não determina
  elegibilidade por si só. Não adicionar enchimento para satisfazer 700 palavras.
- Título inicial idêntico é removido somente na renderização do corpo; evita
  repetir o título da prévia/post sem alterar o Markdown/hash original.
- IDs numéricos de URLs e numeração de lista não são quantidades factuais.
  O verificador continua detectando preço/número novo em prosa e rótulos de links.
- O adaptador factual foi executado e recusa snapshot ausente/incompatível.
  Não preencher PASS para apagar esse bloqueio. SEM_ALERTAS não é factualidade.

## Prova e limites

72 testes direcionados passaram: oito novos sem site-packages (python -S) e 64
regressões de importação/core/prontidão/SEO/gates/handoff RSS. Incluem execução do
CLI em processo novo, sem Groq/WP instalados, rejeição de flags de escrita, rede
negada por mock, imutabilidade, tabela HTML e falsos positivos numéricos. Não somar
reexecuções. O job público de verificação offline existente inclui esses oito;
não há novo workflow/cron ou exposição de artigo privado.

O guia REAL foi processado neste executor cloud com python -S. Hash do Markdown
preservado: dc60376f717f76aa314093e2cfed0423753cfb468c97498721313eb23e3099d9.
Handoff versionado: 0b4152b010112027bb02f6e65dd96f1408d5ed5973caaa4fd6b035c080b19e12.
Dez módulos chamados, nenhum provedor/rede/WP. Pacote/HTML/recibo serão guardados
no Conexo OS PRIVADO; não colocar texto não revisado no repositório MKT-RSS público.

Prontidão real: ENRIQUECIMENTO_PENDENTE por imagem licenciada e links internos.
Contrato factual canônico ausente/incompatível e aceite humano continuam pendentes;
alertas numéricos SEM_ALERTAS não os resolvem. Imagem não foi instalada, prévia
não é o tema WordPress e rascunho remoto não foi criado. Não declarar publicação,
checagem visual em aparelho ou execução de módulos de imagem/entrega não chamados.

Próxima verificação concreta: conferir imagens/licenças e links genuínos, completar
rastreabilidade factual compatível com guia e só então preparar entrega supervisionada.
A responsabilidade por isso é do fluxo do projeto, não de uma ferramenta de IA.
