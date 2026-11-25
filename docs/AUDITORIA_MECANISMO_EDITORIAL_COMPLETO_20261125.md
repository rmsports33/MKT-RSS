# AUDITORIA INTEGRAL DO MECANISMO EDITORIAL — 25/11/2026

**Pergunta do proprietário:** por que o texto do #9900 ficou vago/desconexo; por que
artigos reescritos por outras ferramentas de IA tiveram qualidade diferente dos
totalmente gerados; auditar todo o mecanismo.

**Escopo:** somente leitura em produção (WordPress autenticado, GET) e leitura de
código/documentos locais. Nenhuma escrita, aprovação ou publicação.

---

## 1. Levantamento nos rascunhos reais do WordPress

Varredura autenticada de **149 rascunhos** (`GET /wp-json/wp/v2/posts?status=draft&context=edit`, paginado):

| Achado | Número |
|---|---|
| Com marca de proveniência `cxeg-package:v1` | **2** (#9900 e #9906) |
| Sem marca de proveniência | **147** |
| `voice_status` dos marcados | `NOT_APPLIED` (2/2) |
| `substance_status` dos marcados | `PENDING` (2/2) |
| `image_rights_confirmed` dos marcados | `false` (2/2) |

Os dois únicos rascunhos com marca são justamente os que passaram pelo pacote do
motor em 17/11. Ambos ficaram no mesmo estado: voz não aplicada, avaliação
substantiva pendente, direitos de imagem não confirmados.

A busca por palavras como "ChatGPT", "OpenAI" e "Codex" no corpo dos rascunhos
encontrou 4 ocorrências, mas **são assunto do artigo** (posts 9302 e 9304 falam
sobre produtos da OpenAI), não prova de autoria. Não há marca de proveniência
de outras ferramentas nesses rascunhos.

## 2. Gerados x reescritos — a diferença real não é a ferramenta, é a prova

| Caso | Origem | Registro de voz | Substância | Resultado |
|---|---|---|---|---|
| #9810–#9817 (12/11) | 6 rascunhos do motor, com pacote, recibo, imagem licenciada e avaliação assistida com notas | prova de prompt/DNA nos recibos (`dna_prompt_sha256`) | avaliação substantiva com notas e justificativas | `PRONTO_PARA_REVISAO_HUMANA` em vários; pendências documentadas |
| #9813 | `authoring: codex_assisted`, `external_provider_called: false` — texto **reescrito** por Codex | **`ASSISTED_ADAPTED`**, `method: assisted_editorial_adaptation`, `provider_id: codex`, `dna_prompt_sha256: dd52370e…`, `markdown_sha256` vinculado | **`PASS`**, 5 critérios com nota 3, `review_valid: true` | `PRONTO_PARA_REVISAO_HUMANA`, `pendencias: []` |
| #9900 | texto escrito fora do motor e depois **regerado** pelo pacote canônico | **`NOT_APPLIED`** | **`PENDING`** | `ENRIQUECIMENTO_PENDENTE`; não pronto |

Conclusão: **a ferramenta não determina a qualidade.** O que determina é ter ou
não ter fornecido a prova de adaptação (hash do DNA/prompt ligado ao hash exato
do Markdown) e uma avaliação substantiva com trechos/justificativas. O #9813 é
um texto reescrito por outra ferramenta que **passou** porque trouxe essa prova.
O #9900 é um texto do próprio motor que **não passou** porque a prova não foi
gerada. Isso confirma e corrige a observação do proprietário: o problema é o
caminho sem prova, não o nome da IA.

## 3. Cadeia causal do #9900

1. **17/11** — o texto foi escrito "fora do motor, sem manifesto"
   (`docs/REGENERACAO_MOTOR_20261117.md`) e levado ao WordPress por
   `tools/stage_artigo_draft.py` com uma credencial de editor (`GARGALO_RASCUNHO_WORDPRESS_20261117.md`).
2. **17/11** — o motor regenerou os rascunhos e substituiu o corpo: pacote com
   `version_sha256=34d79ca353fe4f…`, `content_sha256=d814a82573834d…`, módulos
   `EXECUTED`. O motor reportou `ENRIQUECIMENTO_PENDENTE`: voz `NOT_APPLIED`,
   substância `PENDING`, imagem/direitos pendentes. "Nenhum desses itens virou PASS".
3. **19/11** — `modified` do post; marca `cxeg-package:v1` presente no corpo.
4. **22/11** — descobriu-se o defeito de renderização: `mkt_flow_p0/format.py::_markdown_blocos`
   emitia um `<p>` por linha de origem e fechava a lista a cada linha; a
   continuação do item caía fora do `<li>`. No #9900: **51 `<p>`, 4 `<ol>`, 3 `<ul>`**
   onde cabiam 14 `<p>`, 2 `<ol>` e 1 `<ul>`. A correção foi feita no código e
   testada (146 testes), **mas não houve escrita no WordPress** — o registro diz
   explicitamente: "Nenhuma escrita em WordPress: o proprietário pediu para não gravar ainda".
5. **23/11** — `linguagem_validator.py` passou a detectar 75 alertas no #9900
   (50 tipografia, 25 gramática). Política: **sinaliza, nunca bloqueia** a gravação
   de rascunho nem autoriza publicação.
6. **25/11** — o post segue sem parecer humano no Gate; a cadeia CAS está pronta,
   mas não há aprovação válida para publicar.

## 4. Pontos onde a qualidade se perdeu

| # | Ponto | Evidência |
|---|---|---|
| 1 | Texto de origem escrito fora do motor | `REGENERACAO_MOTOR_20261117.md:6` |
| 2 | Caminho de importação/reescrita sem prova de adaptação → `NOT_APPLIED` | marca `voice_status` no corpo; regra em `AGENTS.md:75` e `docs/EDITORIAL_ORCHESTRATION_GATE_20261110.md:11-14` |
| 3 | `EXECUTED` tratado como se fosse aprovação — não é | marca do pacote; `REGENERACAO_MOTOR_20261117.md:21-22` |
| 4 | Avaliação substantiva nunca fechada | `substance_status: PENDING` |
| 5 | Renderizador partindo frases e listas | `REGISTRO_UNICO:571-577`; correção em `format.py` não aplicada ao rascunho vivo |
| 6 | Validador de linguagem apenas alerta | `REGISTRO_UNICO:588-589` |
| 7 | Tabela de fontes sem URLs; afirmações preenchidas por dedução | corpo do #9900; 5 afirmações com trecho literal em `PAUTAS_SELECIONADAS_20261117.md:64-72` |
| 8 | Direitos de imagem não confirmados no pacote | `image_rights_confirmed: false` (embora exista mídia 9912 com licença CC BY 4.0 registrada em `REGISTRO_UNICO:570` — o pacote não a reconhece) |
| 9 | Recibo de versão não reproduzível | `REGISTRO_UNICO:576`: `d814a825…` não foi reproduzido a partir dos insumos locais |
| 10 | Nenhum parecer humano no Gate | varredura autenticada: os 78 rascunhos elegíveis retornaram `HUMAN_REVIEW_RECORD_MISSING` |

## 5. Implementado mas desconectado do fluxo real

- Reparo de parágrafos (`format.py`, `html_paragrafos.py`) — testado, **não aplicado** ao #9900/#9906.
- Validador de linguagem — integrado ao pipeline, mas **não bloqueia** rascunho.
- Avaliação substantiva — existe e já produziu `PASS` em #9813, mas não foi executada para #9900.
- Certificado factual e cadeia CAS — implementados e testados, mas **sem parecer humano** não têm o que validar.
- Chave do Gate — agora configurada, mas isso não cria aprovação.

## 6. Mapeamento de código — por que cada status aparece

**Regra central:** a "voz" não é inferida do conteúdo nem do nome da marca nos
metadados. É um **recibo com formato fechado**, validado em
`mkt_flow_p0/editorial_identity.py:40-99`.

| Mecanismo | Arquivo:linha | Consequência |
|---|---|---|
| Texto pronto sem prova | `editorial_identity.py:47-48` | Normaliza para `NOT_APPLIED`. Não existe "aplicação automática" a partir de metadados. |
| Prova obrigatória | `editorial_identity.py:53,65,85-94` | Exige `{status, method, dna_prompt_sha256, prompt_sha256}` com hash do DNA canônico. |
| Adaptação assistida/humana | `editorial_identity.py:56,67-84,250-253` | Exige `dna_prompt_sha256` + `content_sha256` do **Markdown exato**. |
| Edição depois da prova | `editorial_identity.py:333-336` | Zera `ASSISTED_ADAPTED`/`HUMAN_ADAPTED`, **mas mantém `PROMPT_APPLIED`** — o hash continua se referindo ao prompt original, não ao texto final com atribuição e links. |
| Geração RSS | `rewriter.py:215-221,319-332` | É o único produtor automático de `PROMPT_APPLIED`; calcula o hash dos messages reais enviados ao provedor. |
| Sem URL de fonte | `rewriter.py:319`; `pipeline_rss.py:409-411` | Handoff não existe; rascunho bloqueado por `handoff_editorial_ausente`. |
| Importação | `editorial_import.py:35-40,20` | A prova é **opcional no payload**; omiti-la não gera erro, só perda de status. |
| `--offline` | `editorial_import.py:86-89`; `pipeline_rss.py:650-651` | Congela o texto e o status; `--adapt-editorial` é incompatível. |
| Falha da crítica | `editorial_development.py:168-179` | `review=None`, mas o recibo ainda diz `EXECUTED` — qualidade não revalidada. |
| Substância | `editorial_substance.py:99-125` | Exige `content_sha256`, `brief_sha256`, `method`, `reviewer`, 5 critérios, trechos literais e nota ≥3; qualquer divergência devolve `PENDING`. |
| Bloqueio de voz | `editorial_readiness.py:121-122` | `persona_editorial_nao_aplicada`. |
| Prontidão ≠ publicação | `editorial_readiness.py:151-165` | `PRONTO_PARA_REVISAO_HUMANA` mantém revisão de voz, revisão factual e `pronto_para_publicar=false`. |
| Marca no corpo | `editorial_provenance.py:26-40,43-65` | `validar()` recusa voz não aplicada, substância pendente e imagem sem direitos; a marca **não registra provedor nem modelo**. |
| Transporte | `editorial_transport.py:114-129` | `publish/schedule` exigem avaliação substantiva; `stage/draft` permanecem compatíveis com pendências. |

**Correção importante ao relatório anterior:** `docs/REGENERACAO_MOTOR_20261117.md:60-63`
registra que o checkout do servidor estava em branch antiga e que **foram copiados
apenas `editorial_import.py` e `editorial_provenance.py`**. Portanto a
"regeneração pelo motor" do #9900 foi, na prática, uma **importação com runtime
parcial** — o redator `rewriter.py` não participou. Isso explica diretamente
`NOT_APPLIED` e corrige a atribuição feita na primeira versão desta auditoria.

### Implementado mas desconectado do fluxo real

- `html_paragrafos.py:90-103` — `reparar_paragrafos` é chamado **somente pelos testes**; em produção, `linguagem_validator.py:916-934` usa apenas `listas_seguidas`, como alerta.
- `linguagem_validator.py:967-1029` — `verificar_voz_editorial_mda` **não é chamado** por `pipeline_rss.py`, embora `REGISTRO_UNICO:606` afirme integração. Divergência documentação × código.
- `editorial_identity.py:54-99` — existem validadores para `ASSISTED_ADAPTED`, `HUMAN_ADAPTED` e `external_provider.system_prompt`, mas **nenhum módulo de produção constrói esses objetos**; só testes (`tests/test_editorial_substance.py:220-229`).
- `chatgpt_work_handoff.py:19-77` — sempre devolve `acao=bloqueado` e `verificacao_factual=NAO_VERIFICADO`; sem ligação com `editorial_import.py`.
- `redator-artigo-blogs/src/evergreen.py:24-31,55-76` — subsistema separado (OpenRouter → Groq → Ollama) registra `provedor`/`modelo`, mas **não emite hashes de DNA/prompt nem `editorial_voice_application`**.
- `editorial_package_handoff.py` — usado apenas para vincular SEO (`editorial_core_offline.py:226`); não concede voz nem substância.
- `.github/workflows/daily.yml:50` — executa somente `--queue-only`; geração real depende de disparo manual.
- Cadeia CAS/Gate V1 — cliente e backend implementados, mas integração final e atomicidade concorrente não executadas.

## 7. Conclusão

O defeito do #9900 não é "a IA escreveu mal" de forma isolada. É uma **sequência
de lacunas verificáveis**: origem fora do motor → importação com runtime parcial → ausência de prova de voz →
substância pendente → renderizador partindo o HTML → alertas de linguagem que
não bloqueiam → fontes sem link → sem parecer humano. Cada etapa deixou passar
o que a seguinte deveria ter barrado.

A comparação com #9813 mostra que o mecanismo **sabe** lidar com texto reescrito
por outra IA — desde que a prova de adaptação e a avaliação substantiva sejam
fornecidas. O que faltou no #9900 foi executar esse caminho, não trocar de modelo.

Nada nesta auditoria alterou post, aprovou conteúdo ou autorizou publicação.
